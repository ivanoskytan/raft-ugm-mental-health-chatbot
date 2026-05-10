import json
import logging
from chatbot_engine.llm_client import GPTClient


class PhaseTwoDialogExpansion:
    def __init__(self, api_key, model="gpt-4o"):
        self.gpt_client = GPTClient(api_key=api_key, model=model)
        self.logger = logging.getLogger("PhaseTwoDialogExpansion")

    def run(self, personas):
        conversations = []

        system_prompt = """
You are a clinical dialog generator.

Return ONLY valid JSON. No markdown. No explanations.

Generate ONE object with keys:
{
  "assistant_question": "...",
  "user_answer": "...",
  "grouped_questions_score": {
      "section": "...",
      "scoring_system": [...],
      "data": [
        {
            "survey_question": "...",
            "score": ...
        },
        {
            "survey_question": "...",
            "score": ...
        },
        {
            "survey_question": "...",
            "score": ...
        }
      ],
  }
}

Rules:
- Rephrase every question in the grouped questions as single concrete question naturally in Indonesian but preserve each question's meaning
- Refer to the persona information to tailor the questions and answers appropriately
- Put the scoring system in the output as is
- Generate the user answer in Indonesian as if the persona is answering naturally. Make sure the answer reflects the persona's background and situation.
- Provide a grouped_questions_score using the scoring system for the section and the user answer
"""

        for persona in personas:
            messages = []

            messages.append({
                "role": "assistant",
                "content": f"Halo {persona['name']}, terima kasih sudah meluangkan waktu hari ini. Aku ingin memulai dengan beberapa pertanyaan tentang perasaanmu belakangan ini. Boleh ya?"
            })
            messages.append({"role": "user", "content": "Tentu, saya siap menjawab."})

            for section_name in persona["sections"]:
                if section_name not in persona["question_map"]:
                    continue

                section_data = persona["question_map"][section_name]
                scoring_system = section_data.get("scoring_system", [])

                for group in section_data.get("grouped_questions", []):
                    user_prompt = {
                        "persona": persona["persona"],
                        "section": section_name,
                        "grouped_questions": group.get("questions", []),
                        "scoring_system": scoring_system
                    }
                    raw_output = self.gpt_client.run_prompt(system_prompt, json.dumps(user_prompt, ensure_ascii=False))

                    try:
                        data = json.loads(raw_output)
                    except json.JSONDecodeError as e:
                        logging.error(
                            f"""PhaseTwo JSON parse failed for dialog_id={persona.get('dialog_id')} section={section_name} group='{group.get("group_id")}': {e}"""                        )
                        continue

                    messages.append({"role": "assistant", "content": data.get("assistant_question", "")})
                    messages.append({"role": "user", "content": data.get("user_answer", "")})
                    messages.append({"role": "assistant", "content": data.get("grouped_questions_score", {})})

            messages.append({
                "role": "assistant",
                "content": "Terima kasih sudah berbagi. Apakah ada yang ingin kamu sampaikan sebelum kita akhiri percakapan?"
            })
            messages.append({"role": "user", "content": "Tidak, terima kasih."})
            messages.append({
                "role": "assistant",
                "content": {
                    "section": "Ending",
                    "survey_question": "Sejauh ini, bagaimana perasaanmu setelah menjawab pertanyaan-pertanyaan tadi?",
                    "score": 5
                }
            })

            conversations.append({
                "dialog_id": persona.get("dialog_id"),
                "name": persona.get("name"),
                "messages": messages
            })

        return conversations
