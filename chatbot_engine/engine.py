from config.config import Settings
from chatbot_engine.llm_client import GPTClient
from chatbot_engine.retriever import Retriever

import os
import json
import logging

settings = Settings.load()

class ChatbotEngine:
    def __init__(self):
        self.fine_tuned_model_client = GPTClient(
            api_key=settings.OPENAI_API_KEY,
            model=settings.FINE_TUNED_MODEL
        )
        self.logger = logging.getLogger("ChatbotEngine")
        self.retriever = Retriever()
        return
    
    def generate_response(self, user_query):
        user_answer = user_query.get("user_answer", "")
        group_id = user_query.get("group_id", "")
        section = user_query.get("section", "")
        prev_assistant_response = user_query.get("prev_assistant_response", "")

        system_prompt = """
You are a strict mental health screening assistant operating as a deterministic JSON engine.
Your objective is to generate an internal Chain-of-Thought (CoT), assign diagnostic scores, and construct the ideal conversational assistant response based on the screening phase section.

You will receive a JSON input containing:
- type ("Opening" or "Survey")
- next_section
- user_answer
- next_group_id
- current_questions
- next_questions
- scoring_system
- set_of_documents

DYNAMIC SCORING ENGINE RULE:
For scoring ("Survey" and "Ending" types), evaluate the provided `scoring_system` array against the `user_answer`. Match the intent, frequency, or intensity of the answer against the text in the `description` fields, extract the exact numerical `score`, and assign it to the matching item(s) in `current_questions`. If `current_questions` is empty or the user answer is purely an introduction/name, assign an empty array `[]` to the scores output.

Determine the operational branch based on the payload details:

BRANCH A: If type is "Opening" (or if the user is introducing their name / current_questions is empty)
- Do NOT perform document/RAG evaluation.
- Address the user by name if provided in the user_answer.
- VARIATION & CONCRETE REPHRASING RULE: Do NOT use repetitive formulas like "Saya memahami bahwa...". Instead, use a direct, warm conversational greeting or situational acknowledgment, then情 synthesize the entire `next_questions` array into ONE elegant, overarching thematic question.
- Pattern Example: "Salam kenal Ivan, mari kita mulai dengan melihat sejauh mana perasaan tidak bahagia atau putus asa ini memengaruhi Anda belakangan ini?"
- Output Schema:
{
  "chain_of_thought": "...",
  "assistant_question": "..."
}

BRANCH B: If type is "Survey" AND current_questions is NOT empty
Execute these steps sequentially:
1. RAFT Evaluation & Grounding: Analyze the provided `set_of_documents`. If `set_of_documents` is empty or invalid, skip this step. Otherwise, identify the specific chunk containing the core definition or validation guidelines required to contextualize the `user_answer`. Label this chunk as the 'Oracle' inside your chain of thought.
2. Conversational Clinical Bridging: Extract a subtle validation token from the Oracle document. Instead of formal therapy speak ("Saya memahami bahwa...", "Berdasarkan dokumen...") or textbook diagnostics ("sesuai dengan usia Anda"), transform the clinical insight into a highly natural, human premise clause using smooth openings like "Fluktuasi...", "Wajar jika...", "Perubahan...", or "Kondisi...".
3. Fluid Synthesis: Synthesize the concepts from the `next_questions` array into a single concise inquiry. Merge your clinical bridge clause and this inquiry into at max two compound sentences using smooth connectors like ", jadi...", ", lalu...", or ", namun...". Do NOT list raw symptom strings.
- Output Schema:
{
  "scores": [
    { "survey_question": "<question>", "score": <number> }
  ],
  "chain_of_thought": "...",
  "assistant_question": "..."
}

BRANCH C: If next_section is "Ending" (or conversation is wrapping up)
- Do NOT perform further screening question generation.
- For each item in `current_questions`, assign a final score dynamically from the `scoring_system`.
- Provide a concise closing message offering empathetic, grounded advice based on the best-fit document. Express sincere gratitude for their openness.
- Output Schema:
{
  "scores": [
    { "survey_question": "<question>", "score": <number> }
  ],
  "chain_of_thought": "...",
  "assistant_question": "..."
}

CRITICAL RULES FOR THE JSON STRUCTURE:
1. 'chain_of_thought': Must be written in Indonesian. Document the evaluation logic corresponding to the active branch (e.g., scoring derivation, reasoning for empty lists, Oracle selection, or conversational structural reasoning). Do NOT use second-person pronouns.
2. 'assistant_question': Written in Indonesian using a formal but deeply human clinical tone ("Saya" and "Anda").
3. ABSOLUTE SENTENCE LIMIT: The `assistant_question` MUST be EXACTLY AT MAX TWO sentences long. The entire text must contain ONLY ONE closing punctuation mark (either '.' or '?') at the very end. No paragraph breaks.
4. ANTI-ROBOTIC MANDATE: Avoid cold, text-book, or clinical-manual definitions (e.g., "beraktivitas sehari-hari", "sesuai ekspektasi usia"). The question must flow conversationally like an organic dialogue with a real therapist while maintaining strict brevity.

Return ONLY a valid, minified JSON object matching the requested schema branch. Do not wrap in markdown blocks, do not add trailing text.
"""

        conversation_type = "Opening" if section == "" else "Survey"
        BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
        grouped_mental_health_screening = os.path.join(BASE_DIR, "external_data", "grouped_mental_health_screening.json")

        with open(grouped_mental_health_screening, "r", encoding="utf-8") as f:
            grouped_questions = json.load(f)

        next_questions = []
        scoring_system = []

        section_group_map = {
            "Depression": 2,
            "Anger": 2,
            "Mania": 4,
            "Anxiety": 2,
            "Somatic": 6,
            "Suicidal": 2,
            "Psychosis": 7,
            "Sleep Disturbance": 1,
            "Memory": 5,
            "Dissociation": 6,
            "Substance Use": 4,
            "Repetitive Thought": 3
        }

        # section_group_map = {
        #     "Depression": 2, "Anger": 2
        # }
        sections = list(section_group_map.keys())

        if section == "Opening":
            next_section = "Depression"
            next_group_id = 1
        # elif section == "Anger" and group_id == 2:
        #     next_section = "Ending"
        #     next_group_id = 0
        elif section == "Repetitive Thought" and group_id == 3:
            next_section = "Ending"
            next_group_id = 0
        else:
            current_index = sections.index(section)
            max_group = section_group_map[section]

            if group_id < max_group:
                next_section = section
                next_group_id = group_id + 1
            else:
                if current_index + 1 < len(sections):
                    next_section = sections[current_index + 1]
                    next_group_id = 1
                else:
                    next_section = None
                    next_group_id = None

        current_questions = []
        for item in grouped_questions:
            if item["section"] == section:
                for group in item["grouped_questions"]:
                    if group["group_id"] == group_id:
                        current_questions = group.get("questions", [])

        if next_section != "Ending":
            for item in grouped_questions:
                if item["section"] == next_section:
                    scoring_system = item.get("scoring_system", [])
                    for group in item["grouped_questions"]:
                        if group["group_id"] == next_group_id:
                            next_questions = group.get("questions", [])

        set_of_documents = []
        if section != "Opening":
            contextual_query = f"{section} screening assessment. Question: {prev_assistant_response}. User answer: {user_answer}"
            set_of_documents = self.retriever.run(
                query=contextual_query,
                aspect=section,
            )
        
        self.logger.info(f"Questions for section '{next_section}' and group '{next_group_id}': {next_questions}")

        content_payload = {
            "type": conversation_type,
            "section": next_section,
            "user_answer": user_answer,
            "scoring_system": scoring_system,
            "set_of_documents": json.dumps(set_of_documents),
            "current_questions": current_questions,
            "next_questions": next_questions,
        }

        print(f"Content payload: {json.dumps(content_payload, indent=2)}")
        self.logger.info(f"Processing with content payload: {content_payload}")
        
        raw_response = self.fine_tuned_model_client.run_prompt(
            system_prompt=system_prompt,
            user_prompt=json.dumps(content_payload),
            temperature=0.4
        )

        try:
            response = {
                "model": json.loads(raw_response.strip()),
                "next_group_id": next_group_id,
                "next_section": next_section
            }

            return response
        except json.JSONDecodeError:
            return {
                "error": "[Chatbot Engine]: Model returned invalid JSON format"
            }
