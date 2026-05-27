from chatbot_engine.llm_client import GPTClient
import json
import logging

class PhaseFourCoTAugmentation:
    def __init__(self, api_key, model="gpt-4o"):
        self.gpt_client = GPTClient(api_key=api_key, model=model)
        self.logger = logging.getLogger("PhaseFourCOTAugmentation")
        
    def generate_raft_cot(self, section, current_context_question, user_answer, upcoming_base_question, scoring_system=None, reference_texts=None):
        system_prompt = """
You are a RAFT (Retrieval-Augmented Fine-Tuning) Dataset Expert specializing in clinical psychology and structured JSON formatting.
Your objective is to generate an internal Chain-of-Thought (CoT) and construct the ideal conversational assistant response based on the screening phase section.

Determine the operational branch based on the provided 'Section':

BRANCH A: If Section is "Opening"
- Do NOT perform RAG evaluation. 
- Rewrite the provided 'UPCOMING BASE QUESTION' to add a warm, inviting clinical opening (e.g., "Bagus, mari kita mulai ya. Mengenai perasaan seperti..."). 
- Smoothly connect this warm intro directly into that upcoming question as exactly ONE cohesive sentence or highly natural, non-fragmented phrase flow.

BRANCH B: If Section is "Ending"
- Do NOT perform RAG evaluation.
- Completely rephrase the provided 'UPCOMING BASE QUESTION' text to gracefully end the entire clinical conversation.
- Focus on leaving the user feeling relieved, validated, and grounded. Express sincere gratitude to the user for taking their time and being open.

BRANCH C: If Section is "Survey" (Standard RAG Flow)
Execute these two tasks sequentially:
  TASK 1: RAFT Evaluation & Grounding
  - Analyze the provided 'RETRIEVED REFERENCE CHUNKS'. 
  - Identify which specific chunk contains the core clinical definition, therapeutic framework, or validation guidelines required to contextualize the 'USER ANSWER' (which was given in response to 'QUESTION USER JUST ANSWERED'). Label this chunk as the 'Oracle'.
  - Identify the remaining chunks that are irrelevant or noisy for this specific interaction. Label them as 'Distractors'.

  TASK 2: Clinical Empathy Prefixing
  - Review your identified 'Oracle' chunk to see how a professional clinician validates or normalizes this specific symptom presentation.
  - Formulate an ultra-brief, warm empathy statement derived directly from that clinical insight.
  - Prepend this empathetic validation prefix to the clean, unmodified 'UPCOMING BASE QUESTION' provided. 
  - You MUST combine them into exactly ONE compound sentence using a smooth conversational transition (e.g., [Empathy prefix] + ['; namun ', '; lalu ', ' dan '] + [The unmodified upcoming base question]). No multiple sentences or breaks.

CRITICAL RULES FOR THE JSON STRUCTURE:
1. 'chain_of_thought': Must be written in Indonesian. It is internal clinical reasoning only. Do NOT address the user or use second-person pronouns (Anda, kamu). It must explicitly document the evaluation logic corresponding to the active branch (e.g., if Opening/Ending, explain the conversational positioning; if Survey, explicitly detail the Oracle/Distractor choices and how the clinical empathy style was extracted).
2. 'assistant_question': Written in Indonesian. The final conversational output string generated from Branch A, B, or C.

Return ONLY a valid, minified JSON object matching the schema below. Do not wrap in markdown blocks, do not add trailing text.
{
    "chain_of_thought": "...",
    "assistant_question": "..."
}
"""

        user_prompt = f"""
SCREENING CONTEXT:
Section: {section}
QUESTION USER JUST ANSWERED (The context for their reply): {current_context_question}
USER ANSWER: {user_answer}

SCORING SYSTEM RUBRIC:
{scoring_system if scoring_system else "N/A"}

UPCOMING BASE QUESTION (Prepend the empathy prefix directly to this clean string):
{upcoming_base_question}

RETRIEVED REFERENCE CHUNKS:
{reference_texts if reference_texts else "N/A"}
"""

        response = self.gpt_client.run_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        try:
            cleaned_response = response.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned_response)
        except Exception as e:
            self.logger.error(f"JSON parsing error in RAFT payload: {e} | Raw Response: {response}")
            raise

    def run(self, refined_dialogs):
        augmented_dialogs = []

        for dialog in refined_dialogs:
            dialog_id = dialog.get("dialog_id")
            self.logger.info(f"Augmenting dialog_id={dialog_id} with RAFT methodology")

            augmented_messages = []
            messages = dialog.get("messages", [])
            
            running_assistant_question = None

            for idx, msg in enumerate(messages):
                msg_type = msg.get("type")
                
                if running_assistant_question is None:
                    current_context_question = msg.get("assistant_content", "")
                else:
                    current_context_question = running_assistant_question

                if idx + 1 < len(messages):
                    upcoming_base_question = messages[idx + 1].get("assistant_content", "")
                else:
                    upcoming_base_question = msg.get("assistant_content", "")

                if msg_type == "Opening":
                    try:
                        raft_output = self.generate_raft_cot(
                            section="Opening",
                            current_context_question=current_context_question,
                            user_answer=msg.get("user_content", ""),
                            upcoming_base_question=upcoming_base_question
                        )
                        
                        augmented_messages.append({
                            "type": "Opening",
                            "user_content": msg.get("user_content", ""),
                            "cot_augmentation": raft_output["chain_of_thought"],
                            "current_assistant_response": current_context_question,
                            "following_assistant_response": raft_output["assistant_question"]
                        })
                        
                        running_assistant_question = raft_output["assistant_question"]
                    except Exception as e:
                        self.logger.error(f"Failed processing Opening node: {e}")
                        augmented_messages.append(msg)
                    continue

                if msg_type == "Survey":
                    documents = msg.get("set_of_documents", [])
                    scoring_system = msg.get("scoring_system", [])
                    
                    formatted_refs = ""
                    for doc in documents:
                        formatted_refs += f"--- CHUNK {doc['rank']} (Similarity Score: {doc['score']:.4f}) ---\n{doc['chunk']}\n\n"

                    try:
                        raft_output = self.generate_raft_cot(
                            section=msg.get("section", "Survey"),
                            current_context_question=current_context_question,
                            user_answer=msg.get("user_content", ""),
                            upcoming_base_question=upcoming_base_question, # Pristine next target question
                            scoring_system=scoring_system,
                            reference_texts=formatted_refs
                        )

                        augmented_messages.append({
                            "type": "Survey",
                            "section": msg.get("section"),
                            "user_content": msg.get("user_content"),
                            "scoring_system": scoring_system,
                            "set_of_documents": documents, 
                            "cot_augmentation": raft_output["chain_of_thought"],
                            "question_group_scores": msg.get("grouped_questions_score", []),
                            "current_assistant_response": current_context_question,
                            "following_assistant_response": raft_output["assistant_question"]
                        })

                        running_assistant_question = raft_output["assistant_question"]

                    except Exception as e:
                        self.logger.error(f"PhaseFour RAFT generation failed for dialog_id={dialog_id}: {e}")
                        augmented_messages.append(msg)
                    continue

                if msg_type == "Ending":
                    try:
                        raft_output = self.generate_raft_cot(
                            section="Ending",
                            current_context_question=current_context_question,
                            user_answer=msg.get("user_content", ""),
                            upcoming_base_question=upcoming_base_question
                        )
                        
                        augmented_messages.append({
                            "type": "Ending",
                            "user_content": msg.get("user_content", ""),
                            "cot_augmentation": raft_output["chain_of_thought"],
                            "current_assistant_response": current_context_question,
                            "following_assistant_response": raft_output["assistant_question"]
                        })
                    except Exception as e:
                        self.logger.error(f"Failed processing Ending node: {e}")
                        augmented_messages.append(msg)
                    continue

            augmented_dialogs.append({
                "dialog_id": dialog_id,
                "name": dialog.get("name"),
                "messages": augmented_messages
            })

        return augmented_dialogs