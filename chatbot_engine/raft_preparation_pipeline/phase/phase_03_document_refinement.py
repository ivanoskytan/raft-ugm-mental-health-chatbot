import logging
from chatbot_engine.retriever import Retriever


class PhaseThreeDocumentRefinement:
    def __init__(self, api_key, model="gpt-4o"):
        self.retriever = Retriever()
        self.logger = logging.getLogger("PhaseThreeDocumentRefinement")

    def run(self, dialogs):
        refined_dialogs = []

        for dialog in dialogs:
            dialog_id = dialog.get("dialog_id")
            messages = dialog.get("messages", [])

            refined_messages = []
            i = 0

            while i < len(messages):
                msg = messages[i]

                if (
                    msg["role"] == "assistant"
                    and i + 1 < len(messages)
                    and messages[i+1]["role"] == "user"
                    and not (
                        i + 2 < len(messages)
                        and isinstance(messages[i+2]["content"], dict)
                        and "section" in messages[i+2]["content"]
                    )
                ):
                    refined_messages.append({
                        "type": "Opening",
                        "assistant_content": msg["content"],
                        "user_content": messages[i + 1]["content"],
                    })
                    i += 2
                    continue

                if (
                    msg["role"] == "assistant"
                    and i + 2 < len(messages)
                    and messages[i+1]["role"] == "user"
                    and isinstance(messages[i+2]["content"], dict)
                    and "section" in messages[i+2]["content"]
                ):
                    assistant_question = messages[i]["content"]
                    user_answer = messages[i + 1]["content"]
                    score_obj = messages[i + 2]["content"]
                    section = score_obj.get("section")

                    set_of_documents = []
                    if section and user_answer:
                        try:
                            contextual_query = f"{section} screening assessment. Question: {assistant_question}. User answer: {user_answer}"
                            set_of_documents = self.retriever.run(
                                query=contextual_query,
                                aspect=section,
                            )
                        except Exception as e:
                            self.logger.warning(f"Retriever failed for dialog_id={dialog_id} section={section}: {e}")

                    refined_messages.append({
                        "type": "Survey",
                        "section": section,
                        "assistant_content": msg["content"],
                        "user_content": user_answer,
                        "scoring_system": score_obj.get("scoring_system"),
                        "grouped_questions_score": score_obj.get("data"),
                        "set_of_documents": set_of_documents
                    })

                    i += 3
                    continue

            refined_dialogs.append({
                "dialog_id": dialog_id,
                "name": dialog.get("name"),
                "messages": refined_messages
            })

        return refined_dialogs