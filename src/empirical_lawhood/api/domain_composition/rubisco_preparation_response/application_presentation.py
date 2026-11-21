# SPDX-License-Identifier: MPL-2.0
"""Installed views over original paired preparation and response suppliers."""

from empirical_lawhood.api.application_presentations import ApplicationPresentation
from empirical_lawhood.api.domain_composition.rubisco_response.preparation_presentation import read
from empirical_lawhood.api.domain_composition.rubisco_response.preparation_observation import observe

APPLICATION_PRESENTATION = ApplicationPresentation('rubisco.preparation-response', '1.0.0',
    'Paired preparation and formation response', 'rubisco-preparation-response-v1',
    'programmes/biology/photosynthesis/workflows/rubisco-response/preparation-response-v1.md',
    ('question_id', 'label', 'disposition', 'quantity', 'denominator'), 32, read,
    observe=observe, observation_version='1.0.0')
