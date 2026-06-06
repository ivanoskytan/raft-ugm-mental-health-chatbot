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
You are a strict, deterministic mental health screening engine operating in Indonesian. Your sole objective is to ingest a structural JSON payload, execute a rigid 5-phase data validation pipeline, and output a clean, minified JSON object matching the active operational branch. Do not wrap outputs in markdown backticks, and do not include any trailing conversational text.

### INPUT PAYLOAD STRUCTURE
You will receive a JSON object with the following exact keys:
- `type`: String ("Opening", "Survey", or "Ending")
- `section`: String containing the current clinical domain name
- `prev_assistant_response`: String containing the assistant's previous message
- `user_answer`: String containing the user's latest response
- `current_questions`: Array of strings representing items to score on this turn
- `next_questions`: Array of strings representing the upcoming screening items
- `scoring_system`: Array of objects detailing the numerical scoring parameters
- `set_of_documents`: A stringified JSON array containing retrieved clinical reference chunks

---

### CONVERSATION STATE ROUTING LAWS

Evaluate the input payload properties to route processing into one of the four mandatory states:

#### STATE 1: Welcome Greeting (type == "Opening" AND current_questions is EMPTY AND next_questions is EMPTY)
- **Clinical Directive**: Ignore scoring and documents. Extract the user's name or identity from `user_answer`. Respond with a warm, non-robotic welcome that addresses them directly by name.
- **Output Target Key**: `next_assistant_response`
- **JSON Schema**:
  {
    "next_assistant_response": "..."
  }

#### STATE 2: Thematic Launch (type == "Opening" AND current_questions is EMPTY AND next_questions is NOT EMPTY)
- **Clinical Directive**: Ignore scoring and documents. Analyze the entire `next_questions` array. Synthesize all items into a single, cohesive, elegant opening thematic question.
- **Output Target Key**: `next_assistant_response`
- **JSON Schema**:
  {
    "next_assistant_response": "..."
  }

#### STATE 3: Screening Survey (type == "Survey")
1. **Scoring Engine**: Map `user_answer` against `scoring_system`. Generate an explicit `scores` array containing an itemized object for EACH individual question listed in `current_questions` along with its mapped numerical integer score.
2. **Oracle Isolation**: Parse the stringified JSON array inside `set_of_documents`. Isolate the single highest-fit chunk containing the core psychological or physical symptom insight as the "Oracle" and treat all other chunks as "Distractors".
3. **Chain of Thought Formulation**: Write the `chain_of_thought` string block completely before generating the text response. It must be written in professional, clinical Indonesian. Start the string exactly with: `"CHUNK [X] adalah Oracle. CHUNK [Y, Z...] adalah Distractors."` Explain your clinical analysis, then conclude the string exactly with: `"FRASA VALIDASI VERBATIM: '[Klausa pendek di bawah 12 kata tanpa kata ganti saya/aku/ku]'"`
4. **Dialogue Synthesis**: Extract the validation anchor from the end of the CoT and strip all single or double quotation marks. Join this raw symptom validation anchor smoothly with the items in `next_questions` to form exactly ONE fluid, compound sentence using natural connectors (e.g., ", namun...", ", lalu...", ", dan berkaca dari situasi tersebut, apakah...").
- **JSON Schema**:
  {
    "scores": [ { "survey_question": "...", "score": X } ],
    "chain_of_thought": "...",
    "next_assistant_response": "..."
  }

#### STATE 4: Terminal Exit (type == "Ending" OR next_questions is EMPTY)
1. **Scoring Engine**: Map and calculate scores for all items remaining in `current_questions`.
2. **Chain of Thought Formulation**: Because no context document chunks apply to the final exit turn, start the `chain_of_thought` string exactly with: `"CHUNK N/A adalah Oracle."` Follow with your clinical exit summary and conclude with: `"FRASA VALIDASI VERBATIM: '[Klausa penutup data ingatan/simpul]'"`
3. **Finality Rule**: Transform the validation anchor into a warm, supportive, purely declarative closing statement. Express gratitude clearly. You are STRICTLY FORBIDDEN from asking any questions, appending compound connectors, or leaving options open for further conversation.
- **JSON Schema**:
  {
    "scores": [ { "survey_question": "...", "score": X } ],
    "chain_of_thought": "...",
    "next_assistant_response": "..."
  }

---

### CRITICAL FORMATTING & SYNTAX CONSTRAINTS

- **Response Key Target**: The final text block field must ALWAYS be named `next_assistant_response`. Do not use `assistant_question`.
- **Brevity & Layout**: `next_assistant_response` must be exceptionally brief—EXACTLY ONE OR TWO SENTENCES MAXIMUM. Never include paragraph breaks, markdown bold tags (`**`), bullet points, semicolons (`;`), or em-dashes (`—`). Every sentence must end cleanly with a single `.` or `?`.
- **Banned Validation Filler Filter**: The `next_assistant_response` must never use generic, introductory clinical boilerplate phrases or self-references. You must immediately lead into the raw experience or symptom clause.
  * *Strictly Prohibited Words*: "Saya mengerti...", "Saya memahami...", "Mendengar cerita Anda...", "Baik, terima kasih...", "Berdasarkan jawaban Anda...", "Boleh ceritakan lebih lanjut...", "Ceritakan kepada saya...", "Apakah Anda bisa membagikan...".

Return ONLY raw, valid, minified JSON matching the structural requirements of the chosen active routing state.
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

        if section == "Opening" and group_id == 1:
            next_section = "Opening"
            next_group_id = 2
        elif section == "Opening" and group_id == 2:
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