from chatbot_engine.llm_client import GPTClient
import logging
import json

class PhaseFiveFineTuningFormatting:
    def __init__(self, api_key, model="gpt-4o"):
        self.gpt_client = GPTClient(api_key=api_key, model=model)
        self.logger = logging.getLogger("PhaseFiveFineTuningFormatting")

    def _format_questions_group(self, grouped):
        formatted = []
        for _, item in enumerate(grouped):
            question = item.get("survey_question", "")
            formatted.append(question)
        return formatted

    def run(self, augmented_dialogs):
        fine_tuning_formatted_dialogs = []

        for dialog in augmented_dialogs:
            formatted_messages = []
            messages = dialog.get("messages", [])
            last_section = ""

            for i, msg in enumerate(messages):
                current_section = msg.get("section", "")
                current_group_id = 1
                
                if current_section != last_section:
                    current_group_id = 1
                else:
                    current_group_id += 1
                
                last_section = current_section

                msg_type = msg.get("type")

                next_msg = messages[i+1] if i + 1 < len(messages) else {}
                
                current_questions_group = self._format_questions_group(msg.get("question_group_scores") or [])
                next_questions_group = self._format_questions_group(next_msg.get("question_group_scores") or [])

                if msg_type == "Opening":
                    formatted_messages.append({
                        "role": "user",
                        "content": json.dumps(
                        {
                            "type": "Opening",
                            "section": current_section,
                            "group_id": 0,
                            "current_assistant_response": msg.get("current_assistant_response", ""),
                            "user_answer": msg.get("user_content", ""),
                            "current_questions": current_questions_group,
                            "next_questions": next_questions_group,
                            "scoring_system": next_msg.get("scoring_system", [])
                        }, ensure_ascii=False)
                    })

                    formatted_messages.append({
                        "role": "assistant",
                        "content": json.dumps(
                        {
                            "next_assistant_response": next_msg.get("current_assistant_response", "")
                        }, ensure_ascii=False)
                    })

                elif msg_type == "Survey":
                    formatted_messages.append({
                        "role": "user",
                        "content": json.dumps(
                            {
                            "type": "Survey",
                            "section": current_section,
                            "group_id": current_group_id,
                            "user_answer": msg.get("user_content", ""),
                            "current_assistant_response": msg.get("current_assistant_response", ""),
                            "current_questions": current_questions_group,
                            "next_questions": next_questions_group,
                            "scoring_system": next_msg.get("scoring_system", []),
                            "set_of_documents": msg.get("set_of_documents", [])
                        }, ensure_ascii=False)
                    })

                    formatted_messages.append({
                        "role": "assistant",
                        "content": json.dumps(
                            {
                            "scores": msg.get("question_group_scores", []),
                            "chain_of_thought": msg.get("cot_augmentation", ""),
                            "next_assistant_response": msg.get("following_assistant_response", "")
                        }, ensure_ascii=False)
                    })

            fine_tuning_formatted_dialogs.append({
                "messages": formatted_messages
            })

        return fine_tuning_formatted_dialogs
