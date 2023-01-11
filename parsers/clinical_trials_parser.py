from pytrials.client import ClinicalTrials

from enforce_typing import enforce_types
from dataclasses import dataclass, field
from typing import List
import logging, sys

from helpers import to_link_format

ct_logger = logging.getLogger('clinical_trials')
ct_logger.addHandler(logging.StreamHandler(sys.stdout))
ct_logger.setLevel(logging.INFO)

@dataclass
class Location:
    name: str
    city: str
    country: str

@dataclass
class ReadyClinicalTrial:

    title: str
    nctt_id: str
    link: str = field(init=False)
    description: str
    recruitment_status: str

    completion_date: str
    criteria: str


    locations: List[Location]
    
    def __post_init__(self):
        self.link = f'https://clinicaltrials.gov/ct2/show/{self.nctt_id}'

def parse_clinical_trial(trial):
    
    title = trial['Study']['ProtocolSection']['IdentificationModule']['OfficialTitle']
    nctt_id = trial['Study']['ProtocolSection']['IdentificationModule']['NCTId']
    description = trial['Study']['ProtocolSection']['DescriptionModule']['BriefSummary']
    recruitment_status = trial['Study']['ProtocolSection']['StatusModule']['OverallStatus']
    criteria = trial['Study']['ProtocolSection']['EligibilityModule']['EligibilityCriteria']
    
    try:
        completion_date = trial['Study']['ProtocolSection']['StatusModule']['CompletionDateStruct']['CompletionDate']
    except KeyError as e:
        completion_date = ''

    try:
        locations = trial['Study']['ProtocolSection']['ContactsLocationsModule']['LocationList']['Location']
    except KeyError as e:
        ct_logger.info(f'No locations for {nctt_id}. Key error: {e}')
        locations = []
    
    if locations:
        try:
            locations = [
                Location(
                    name=location['LocationFacility'],
                    city=location['LocationCity'],
                    country=location['LocationCountry']
                )
                for location in locations
            ]
        except KeyError as e:
            ct_logger.info(f'No locations for {nctt_id}. Key error: {e}')
            locations = []

    return ReadyClinicalTrial(
        title=title,
        nctt_id=nctt_id,
        description=description,
        completion_date=completion_date,
        recruitment_status=recruitment_status,
        locations=locations,
        criteria=criteria
    )

def get_last_clinical_trials(query, min_results_num=10):

    ct = ClinicalTrials()
    topic = to_link_format(query)

    for i in range(min_results_num, 105, 5):

        last_clinical_trials = ct.get_full_studies(topic, max_studies=min_results_num)
        last_clinical_trials = last_clinical_trials['FullStudiesResponse']['FullStudies']

        ready_clinical_trials = [
            parse_clinical_trial(trial) for trial in last_clinical_trials
        ]

        found_statuses = set([trial.recruitment_status for trial in ready_clinical_trials])
        if ('Completed' in found_statuses) and ('Recruiting' in found_statuses):
            break

    return [trial for trial in ready_clinical_trials if trial.recruitment_status == 'Recruiting' or trial.recruitment_status == 'Completed']