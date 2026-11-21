"""Small, timeout- and byte-bounded boundary for fixed local diagnostics."""

from __future__ import annotations

import os
import selectors
import signal
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, IO, TypeVar, cast


PROCESS_IO_CHUNK_BYTES = 64 * 1024


class BoundedProcessError(RuntimeError):
    """A fixed local command exceeded or violated its process-I/O contract."""


@dataclass(frozen=True, slots=True)
class BoundedProcessResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def _close_registered(selector: selectors.BaseSelector, stream: IO[bytes]) -> None:
    try:
        selector.unregister(stream)
    except (KeyError, ValueError):
        pass
    stream.close()


def _kill_process_tree(process: subprocess.Popen[bytes]) -> None:
    group_kill_failed = False
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:  # pragma: no cover - the supported production host is POSIX
            process.kill()
    except OSError:
        group_kill_failed = True
    if group_kill_failed and process.poll() is None:
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass


_Output = TypeVar("_Output")


@dataclass(frozen=True, slots=True)
class BoundedProcessStreamResult(Generic[_Output]):
    returncode: int
    output: _Output
    stderr: bytes
    stdout_bytes: int


class BoundedProcessReader:
    """Finite stdout reads with concurrent bounded stderr and stdin service.

    A read returns at most one I/O frame. The consumer must handle short reads;
    unbounded reads are deliberately unavailable. Only the process owner closes
    channels and admits the final return code.
    """

    def __init__(self, process, *, input_bytes, timeout_seconds, maximum_stdout_bytes, maximum_stderr_bytes):
        self.process = process
        self.streams = (process.stdin, process.stdout, process.stderr)
        self.selector = selectors.DefaultSelector()
        self.deadline = time.monotonic() + timeout_seconds
        self.input_bytes = input_bytes
        self.input_offset = 0
        self.maximum_stdout_bytes = maximum_stdout_bytes
        self.maximum_stderr_bytes = maximum_stderr_bytes
        self.stdout_bytes = 0
        self.stderr = bytearray()
        self._pending = bytearray()
        self._stdout_open = True
        for stream in self.streams:
            os.set_blocking(stream.fileno(), False)
        self.selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        self.selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        if input_bytes:
            self.selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
        else:
            process.stdin.close()

    def _remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise BoundedProcessError("bounded local command timed out")
        return remaining

    def _poll(self):
        events = self.selector.select(self._remaining())
        if not events:
            raise BoundedProcessError("bounded local command timed out")
        for key, _mask in events:
            stream = cast(IO[bytes], key.fileobj)
            if key.data == "stdin":
                try:
                    written = os.write(stream.fileno(),
                        self.input_bytes[self.input_offset:self.input_offset + PROCESS_IO_CHUNK_BYTES])
                except BrokenPipeError:
                    written = 0
                self.input_offset += written
                if written == 0 or self.input_offset == len(self.input_bytes):
                    _close_registered(self.selector, stream)
                continue
            stdout = key.data == "stdout"
            used = self.stdout_bytes if stdout else len(self.stderr)
            limit = self.maximum_stdout_bytes if stdout else self.maximum_stderr_bytes
            chunk = os.read(stream.fileno(), PROCESS_IO_CHUNK_BYTES if limit is None else min(PROCESS_IO_CHUNK_BYTES, max(1, limit - used + 1)))
            if not chunk:
                _close_registered(self.selector, stream)
                if stdout:
                    self._stdout_open = False
                continue
            if limit is not None and used + len(chunk) > limit:
                raise BoundedProcessError(f"bounded local command {key.data} exceeds its byte ceiling")
            if stdout:
                self.stdout_bytes += len(chunk)
                self._pending.extend(chunk)
            else:
                self.stderr.extend(chunk)

    def read(self, size):
        if type(size) is not int or size < 0:
            raise ValueError("streamed stdout requires an explicit nonnegative read size")
        if size == 0:
            return b""
        while not self._pending and self._stdout_open:
            self._poll()
        count = min(size, len(self._pending))
        result = bytes(self._pending[:count])
        del self._pending[:count]
        return result

    def finish(self):
        # A consumer may finish parsing before trailing stdout or stderr. Both
        # channels still obey their full ceilings and the original deadline.
        while self.read(PROCESS_IO_CHUNK_BYTES):
            pass
        while self.selector.get_map():
            self._poll()
        try:
            return self.process.wait(timeout=self._remaining())
        except subprocess.TimeoutExpired as error:
            raise BoundedProcessError("bounded local command timed out") from error

    def close(self):
        self.selector.close()
        for stream in self.streams:
            if not stream.closed:
                stream.close()


def run_bounded_stream_command(
    argv: Sequence[str],
    *,
    consume_stdout: Callable[[BoundedProcessReader], _Output],
    cwd: Path | None = None,
    environment: Mapping[str, str] | None = None,
    input_bytes: bytes = b"",
    timeout_seconds: float = 5.0,
    maximum_input_bytes: int = 0,
    maximum_stdout_bytes: int | None = 64 * 1024,
    maximum_stderr_bytes: int = 64 * 1024,
) -> BoundedProcessStreamResult[_Output]:
    """Consume one bounded command without retaining its complete stdout.

    The caller owns the bounded consumer's retained result. Process channel
    buffers retain at most one stdout frame plus the selected stderr ceiling.
    Consumer failure, timeout and success all clean up the owned process group.
    """
    if not argv or any(not isinstance(value, str) or not value for value in argv):
        raise ValueError("bounded process argv must be a nonempty string sequence")
    if not callable(consume_stdout):
        raise TypeError("streamed process requires an explicit stdout consumer")
    if not isinstance(input_bytes, bytes):
        raise ValueError("bounded process input must be immutable bytes")
    if timeout_seconds <= 0:
        raise ValueError("bounded process timeout must be positive")
    if any(value is not None and (type(value) is not int or value < 0)
            for value in (maximum_input_bytes, maximum_stdout_bytes, maximum_stderr_bytes)):
        raise ValueError("bounded process I/O ceilings must be nonnegative")
    if len(input_bytes) > maximum_input_bytes:
        raise BoundedProcessError("bounded local command input exceeds its byte ceiling")
    try:
        process = subprocess.Popen(tuple(argv), cwd=cwd,
            env=None if environment is None else dict(environment), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0,
            start_new_session=os.name == "posix")
    except OSError as error:
        raise BoundedProcessError("bounded local command could not start") from error
    assert process.stdin is not None and process.stdout is not None and process.stderr is not None
    reader = None
    try:
        reader = BoundedProcessReader(process, input_bytes=input_bytes, timeout_seconds=timeout_seconds,
            maximum_stdout_bytes=maximum_stdout_bytes, maximum_stderr_bytes=maximum_stderr_bytes)
        output = consume_stdout(reader)
        returncode = reader.finish()
        # A fixed local command cannot leave background descendants, even when
        # its own parent has returned and closed all channels successfully.
        _kill_process_tree(process)
        return BoundedProcessStreamResult(returncode, output, bytes(reader.stderr), reader.stdout_bytes)
    except BaseException:
        _kill_process_tree(process)
        raise
    finally:
        if reader is not None:
            reader.close()
        else:
            for stream in (process.stdin, process.stdout, process.stderr):
                if not stream.closed:
                    stream.close()


def run_bounded_command(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    environment: Mapping[str, str] | None = None,
    input_bytes: bytes = b"",
    timeout_seconds: float = 5.0,
    maximum_input_bytes: int = 0,
    maximum_stdout_bytes: int | None = 64 * 1024,
    maximum_stderr_bytes: int = 64 * 1024,
) -> BoundedProcessResult:
    """Compatibility boundary for callers that need complete bounded stdout."""
    def collect(reader):
        output = bytearray()
        while chunk := reader.read(PROCESS_IO_CHUNK_BYTES):
            output.extend(chunk)
        return bytes(output)

    result = run_bounded_stream_command(argv, consume_stdout=collect, cwd=cwd, environment=environment,
        input_bytes=input_bytes, timeout_seconds=timeout_seconds, maximum_input_bytes=maximum_input_bytes,
        maximum_stdout_bytes=maximum_stdout_bytes, maximum_stderr_bytes=maximum_stderr_bytes)
    return BoundedProcessResult(result.returncode, result.output, result.stderr)


__all__ = [
    "BoundedProcessError",
    "BoundedProcessResult",
    "BoundedProcessReader",
    "BoundedProcessStreamResult",
    "run_bounded_command",
    "run_bounded_stream_command",
]
