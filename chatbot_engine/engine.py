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
        self.model_client = GPTClient(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o"
        )
        self.logger = logging.getLogger("ChatbotEngine")
        self.retriever = Retriever()
        return
    
    def generate_assistant_response(self, user_query):
        user_answer = user_query.get("user_answer", "")
        group_id = user_query.get("group_id", "")
        section = user_query.get("section", "")
        prev_assistant_response = user_query.get("prev_assistant_response", "")

        system_prompt = """
You are a strict mental health screening assistant operating as a deterministic JSON engine.
Your objective is to execute a strict sequential dependency pipeline: evaluate the clinical context, isolate the single best-fit clinical reference document, document this choice as the first action within the 'chain_of_thought', and directly inject that specific document's clinical insight into the 'assistant_question' without using generic conversational filler.

You will receive a JSON input containing:
- type ("Opening" or "Survey")
- next_section
- user_answer
- next_group_id
- current_questions
- next_questions
- scoring_system
- set_of_documents

CORE DEPENDENCY MANDATES:
1. 'chain_of_thought' (The Foundation): Written in Indonesian from an objective, professional clinical standpoint. This block MUST be generated completely before formulating the final output text. To enforce reference grounding, you MUST follow this exact formatting layout inside this string field:
   - Start the text exactly with: "Dokumen Terpilih: Rank [X] / [Alasan klinis...]" where [X] is the rank number (1-5) of the best-fit chunk from `set_of_documents`. If empty, start with "Dokumen Terpilih: Tidak ada".
   - Follow with your verification of the active routing branch (Branch A, B, or C).
   - Follow with a clinical translation of the user's emotional state based on `user_answer`.
   - Conclude with your explicit linguistic strategy for synthesizing all items in `next_questions` into a single theme.
2. 'assistant_question' (The Causal Output): This field is a strict downstream consequence of the isolated document declared at the start of your 'chain_of_thought'. It must directly incorporate the clinical theme of that selected document. It is forbidden from using open-ended conversation starters or generic supportive filler.

BRANCH DETERMINATION (ROUTING RULES):

BRANCH A: If current_questions is EMPTY (Regardless of 'type' string value)
- State "Dokumen Terpilih: Tidak ada" at the start of your CoT. Do NOT assign scores. Address the user by name if provided in `user_answer`.
- Greet warmly without robotic templates. Synthesize the entire `next_questions` array into ONE elegant, overarching thematic question.
- Output Schema:
{
  "chain_of_thought": "...",
  "assistant_question": "..."
}

BRANCH B: If current_questions is NOT EMPTY AND next_section is NOT "Ending"
1. Scoring: Evaluate `user_answer` against `scoring_system`. Extract the exact numerical `score` for EACH item listed in `current_questions`.
2. Grounded Clinical Bridging: Read the specific document chunk declared at the start of your 'chain_of_thought'. Extract its core physical or psychological symptom insight and transform it directly into a brief, validating opening clause.
   - CRITICAL STRIPPED FORMULA: The clause MUST start directly with the raw emotional or physical experience itself (e.g., "Menghadapi rasa putus asa yang berat...", "Ketika rasa tidak berdaya muncul...", "Perasaan tertekan yang menguras energi..."). Do NOT use any introductory filler, conversational transitions, or self-references ("Saya", "Boleh").
3. Fluid Synthesis: Connect that raw symptom clause directly to a synthesized inquiry that encapsulates ALL items in the `next_questions` array using smooth connectors (", jadi...", ", lalu...", ", namun..."). Do NOT ask open-ended follow-ups; only ask the single synthesized question representing the items in `next_questions`.
- Output Schema:
{
  "scores": [ { "survey_question": "<question>", "score": <number> } ],
  "chain_of_thought": "...",
  "assistant_question": "..."
}

BRANCH C: If next_section is "Ending"
- Assign final scores dynamically from the `scoring_system` for all items in `current_questions`.
- Write a concise closing statement offering grounded advice directly derived from the chosen document, followed by a sincere expression of gratitude.
- FINALITY RULE: This must be purely declarative. Absolutely NO follow-up questions or invitations for further conversation.
- Output Schema:
{
  "scores": [ { "survey_question": "<question>", "score": <number> } ],
  "chain_of_thought": "...",
  "assistant_question": "..."
}

CRITICAL ASSISTANT RESPONSE CONSTRAINTS:
1. Tone & Language: 'assistant_question' must be in Indonesian using an organic therapist tone ("Saya" and "Anda").
2. Strict Brevity: The `assistant_question` MUST be exceptionally concise—EXACTLY ONE OR TWO SENTENCES MAXIMUM. Keep sentences short and direct.
3. Formatting: No paragraph breaks, no bold text, no bullet points. Ensure the response ends cleanly with a period '.' or question mark '?'.
4. BANNED GENERIC FILLER FILTER: Under no circumstances may the `assistant_question` begin with, contain, or transition into generic prompt-extending filler or boilerplate validation templates. 
   - Absolute Banned List: "Saya mengerti...", "Saya memahami...", "Mendengar cerita Anda...", "Baik, terima kasih...", "Berdasarkan jawaban Anda...", "Boleh ceritakan lebih lanjut...", "Ceritakan kepada saya...", "Apakah Anda bisa membagikan...". 
   - You must jump directly into the raw symptom bridge clause as defined in Branch B.

Return ONLY a valid, minified JSON object matching the active branch schema. Do not wrap in markdown blocks, do not add trailing text.
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
            "prev_assistant_response": user_query.get("prev_assistant_response", ""),
            "user_answer": user_answer,
            "current_questions": current_questions,
            "next_questions": next_questions,
            "scoring_system": scoring_system,
            "set_of_documents": json.dumps(set_of_documents),
        }

        print(f"Content payload: {json.dumps(content_payload, indent=2)}")
        self.logger.info(f"Processing with content payload: {content_payload}")
        
        raw_response = self.fine_tuned_model_client.run_prompt(
            system_prompt=system_prompt,
            user_prompt=json.dumps(content_payload),
            temperature=0.4
        )

        print(f"Raw model response: {raw_response}")

        try:
            response = {
                "model": json.loads(raw_response.strip()),
                "next_group_id": next_group_id,
                "next_section": next_section
            }

            return response
        except KeyError as e:
            return {
                "error": f"[Chatbot Engine]: Missing expected key in model response - {str(e)}"
            }
        except json.JSONDecodeError:
            return {
                "error": "[Chatbot Engine]: Model returned invalid JSON format"
            }

    def generate_assessment_summary(self, assessment_result):
        system_prompt = """"
You are an expert clinical psychologist and data analysis engine specializing in mental health screenings. Your input (user prompt) is a JSON payload containing an array of active clinical sections. Each section includes a list of specific questions paired with the user's subjective frequency response description in Indonesian (e.g., "Tidak pernah", "Jarang", "Kadang-kadang", "Sering", "Selalu").

Analyze the provided payload and generate a response that adheres strictly to these guidelines:
1. Language, Perspective & Format: Write the entire response in Indonesian (Bahasa Indonesia) using compassionate, clear, and professional psychological terminology. You must strictly use a third-person point of view (e.g., use "Responden" or "Pengguna" instead of "Anda" or "Kamu"). The output must be exactly a maximum of 2 paragraphs of continuous text. Do not use any headings, bolded section labels, bullet points, markdown tables, or numbered lists.
2. Contextual Accuracy: Base your analysis ONLY on the specific sections and answers present in the payload. Do not assume, hallucinate, or generalize about mental health domains that are absent from the data. 
3. Paragraph 1 (Clinical Synthesis): Provide an empathetic clinical synthesis of the respondent's current baseline. Focus heavily on identifying and correlating notable elevations (responses matching "Sering" or "Selalu") across the active sections. If no high elevations exist, synthesize the prevailing mild/moderate trends.
4. Paragraph 2 (Actionable Support & Disclaimer): Offer tailored, practical self-care recommendations relevant to the elevated trends found in the first paragraph. Conclude the paragraph with a standard medical disclaimer explicitly stating that this screening is not a clinical diagnosis and the respondent should consult a licensed professional for an official evaluation.
        """

        BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
        grouped_mental_health_screening = os.path.join(BASE_DIR, "external_data", "grouped_mental_health_screening.json")

        scoring_lookup = {}
        with open(grouped_mental_health_screening, "r", encoding="utf-8") as f:
            grouped_questions = json.load(f)
            for group in grouped_questions:
                section_name = group.get("section")
                if section_name:
                    scoring_lookup[section_name] = {
                        item["score"]: item["description"] for item in group.get("scoring_system", [])  
                    }

        payload = []
        for item in assessment_result:
            section_name = item.get("section")
            questions = item.get("questions", [])

            section_scores = scoring_lookup.get(section_name, {})
            section_payload = {
                "section": section_name,
                "answers": []
            }

            for q in questions:
                score_val = q.get("score")
                description = section_scores.get(score_val, "Tidak diketahui")

                section_payload["answers"].append({
                    q.get("original_question"): description 
                })

            payload.append(section_payload)

        try:
            response = self.model_client.run_prompt(
                system_prompt=system_prompt,
                user_prompt=json.dumps(payload),
                temperature=0.5
            )
            return response
        except KeyError as e:
            return {
                "error": f"[Chatbot Engine]: Missing expected key in model response - {str(e)}"
            }
        except json.JSONDecodeError:
            return {
                "error": "[Chatbot Engine]: Model returned invalid JSON format for assessment summary"
            }