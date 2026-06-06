import json
import logging
import tqdm
import os

from .phase.phase_01_persona_generation import PhaseOnePersonaGeneration
from .phase.phase_02_dialog_expansion import PhaseTwoDialogExpansion
from .phase.phase_03_document_refinement import PhaseThreeDocumentRefinement
from .phase.phase_04_cot_augmentation import PhaseFourCoTAugmentation
from .phase.phase_05_fine_tuning_formatting import PhaseFiveFineTuningFormatting

class RAFTDataPreparationPipeline:
    def __init__(self, api_key, model="gpt-4o"):
        self.model = model
        self.BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
        self.api_key = api_key
        self.phases = {
            1: ("Persona Generation", PhaseOnePersonaGeneration(api_key, model),
                os.path.join(self.BASE_DIR, "external_data", "grouped_mental_health_screening.json"),
                os.path.join(self.BASE_DIR, "chatbot_engine", "raft_preparation_pipeline", "output", "v4", "phase_01_persona_generation.json")),
            2: ("Dialogue Expansion", PhaseTwoDialogExpansion(api_key, model),
                os.path.join(self.BASE_DIR, "chatbot_engine", "raft_preparation_pipeline", "output", "v4", "phase_01_persona_generation.json"),
                os.path.join(self.BASE_DIR, "chatbot_engine", "raft_preparation_pipeline", "output", "v4", "phase_02_dialog_expansion.json")),
            3: ("Document Refinement", PhaseThreeDocumentRefinement(api_key, model),
                os.path.join(self.BASE_DIR, "chatbot_engine", "raft_preparation_pipeline", "output", "v4", "phase_02_dialog_expansion.json"),
                os.path.join(self.BASE_DIR, "chatbot_engine", "raft_preparation_pipeline", "output", "v4", "phase_03_document_refinement.json")),
            4: ("CoT Augmentation", PhaseFourCoTAugmentation(api_key, model),
                os.path.join(self.BASE_DIR, "chatbot_engine", "raft_preparation_pipeline", "output", "v4", "phase_03_document_refinement.json"),
                os.path.join(self.BASE_DIR, "chatbot_engine", "raft_preparation_pipeline", "output", "v4", "phase_04_cot_augmentation.json")),
            5: ("Final Dataset Formatting", PhaseFiveFineTuningFormatting(api_key, model),
                os.path.join(self.BASE_DIR, "chatbot_engine", "raft_preparation_pipeline", "output", "v4", "phase_04_cot_augmentation.json"),
                os.path.join(self.BASE_DIR, "chatbot_engine", "raft_preparation_pipeline", "output", "v4", "phase_05_fine_tuning_formatting.json")),
        }

    def run_pipeline(self, target_phase=None):
        if target_phase is not None:
            if target_phase not in self.phases:
                raise ValueError("Invalid phase. Must between 1 and 5")
            
            phase_name, phase_obj, input_dir, output_dir = self.phases[target_phase]
            logging.info(f"\n-- Running ONLY Phase {target_phase}: {phase_name} --")

            phase_input = self.load_json(input_dir)
            if phase_input is None:
                raise RuntimeError(f"Missing required file: {input_dir}")
            
            phase_output = phase_obj.run(phase_input)
            self.save_json(output_dir, phase_output)
            return

        for idx, (phase_name, phase_object, input_dir, output_dir) in self.phases.items():
            logging.info(f"\n-- Running Phase {idx}: {phase_name} --")
            phase_input = self.load_json(input_dir)
            if phase_input is None:
                raise RuntimeError(f"Missing required file: {input_dir}")

            phase_output = phase_object.run(phase_input)
            self.save_json(output_dir, phase_output)

    def load_json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as err:
            logging.error(f"Error loading JSON from {path}: {err}")
            return None

    def save_json(self, path, data):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as err:
            logging.error(f"Error saving JSON to {path}: {err}")
            return None
