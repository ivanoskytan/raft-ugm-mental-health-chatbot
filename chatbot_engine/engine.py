from config.config import Settings
from chatbot_engine.llm_client import GPTClient
from chatbot_engine.retriever import Retriever

import os
import json

settings = Settings.load()

class ChatbotEngine:
    def __init__(self):
        self.fine_tuned_model_client = GPTClient(
            api_key=settings.OPENAI_API_KEY,
            model=settings.FINE_TUNED_MODEL
        )
        self.retriever = Retriever()
        return
    
    def generate_response(self, user_query):
        user_answer = user_query.get("user_answer", "")
        group_id = user_query.get("group_id", "")
        section = user_query.get("section", "")

        system_prompt = """
You are a mental health screening assistant.

You will receive a JSON input containing:
- type ("Opening" or "Survey")
- next_section
- user_answer
- next_group_id
- next_questions
- scoring_system
- set_of_documents

GENERAL BEHAVIOR:
- Before generating any response, select the MOST appropriate document from set_of_documents based on the user_answer.
- Use the selected document as a reference to provide brief, empathetic, and relevant advice.
- The advice must feel natural, supportive, and context-aware (not quoted or explicitly referencing the document).
- After giving the advice, continue the conversation by asking the required questions.
- Use the words "Saya" and "Anda" to maintain a formal and polite tone in the response.

If type is "Opening":
1. Generate ONE assistant_question that:
- responds naturally to the user_answer,
- addresses the user by name,
- includes brief empathetic advice informed by the selected document,
- asks every single questions in next_questions within a single conversational message. 
Return ONLY:
{
"assistant_question": "<empathetic response to the user_answer that includes brief advice informed by the most relevant document, and naturally includes every question in the next_questions>"
}

If type is "Survey":
1. Carefully analyze the user_answer.
2. For EACH survey question in next_questions, assign a score.
3. Scores MUST strictly follow the scoring_system provided in the input.
4. Every question in next_questions MUST appear once in the scores list.
5. Select the most relevant document from set_of_documents and use it to generate a brief empathetic advice.
6. Generate ONE assistant_question that:
- responds naturally to the user_answer,
- addresses the user by name,
- includes brief empathetic advice informed by the selected document,
- asks every single questions in next_questions within a single conversational message.

If section is "Ending":
1. Select the most appropriate document from set_of_documents.
2. Provide a meaningful closing message with empathetic advice based on that document.
3. Do not ask further questions.

Return ONLY:
{
"scores": [
    { "survey_question": "<question>", "score": <number following scoring_system> }
],
"assistant_question": "<empathetic response with advice informed by the selected document, followed by all required questions>"
}

STRICT RULES:
- Output valid JSON only.
- Do NOT include explanations.
- Do NOT include extra fields.
- Do NOT wrap JSON in markdown.
        """

        conversation_type = "Opening" if section == "" else "Survey"
        BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
        grouped_mental_health_screening = os.path.join(BASE_DIR, "external_data", "grouped_mental_health_screening.json")

        with open(grouped_mental_health_screening, "r", encoding="utf-8") as f:
            grouped_questions = json.load(f)

        next_questions = []
        scoring_system = []

        section_group_map = {
            "Depression": 2, "Anger": 2, "Mania": 1, "Anxiety": 2, "Somatic": 3,
            "Suicidal": 2, "Psychosis": 2, "Sleep Disturbance": 1, "Memory": 1,
            "Dissociation": 2, "Substance Use": 2, "Repetitive Thought": 2
        }

        # section_group_map = {
        #     "Depression": 2, "Repetitive Thought": 2
        # }
        sections = list(section_group_map.keys())

        if section == "Opening":
            next_section = "Depression"
            next_group_id = 1
        elif section == "Repetitive Thought":
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

        if next_section != "Ending":
            for item in grouped_questions:
                if item["section"] == next_section:
                    scoring_system = item.get("scoring_system", [])
                    for group in item["grouped_questions"]:
                        if group["group_id"] == next_group_id:
                            next_questions = group.get("questions", [])

        set_of_documents = []
        print("ENTER RETRIEVER")
        if section != "Opening":
            set_of_documents = self.retriever.run(
                query=user_answer,
                aspect=section,
            )
            print("Set of documents: ", set_of_documents)

        content_payload = {
            "type": conversation_type,
            "next_section": next_section,
            "user_answer": user_answer,
            "next_group_id": next_group_id,
            "next_questions": next_questions,
            "scoring_system": scoring_system,
            "set_of_documents": json.dumps(set_of_documents),
        }

        print("Prompt payload: ", json.dumps(content_payload))
        
        raw_response = self.fine_tuned_model_client.run_prompt(
            system_prompt=system_prompt,
            user_prompt=json.dumps(content_payload),
            temperature=0.6
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
