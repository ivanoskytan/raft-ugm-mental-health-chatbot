from chatbot_engine.llm_client import GPTClient
import json
import logging
import re

class PhaseFourCoTAugmentation:
    def __init__(self, api_key, model="gpt-4o"):
        self.gpt_client = GPTClient(api_key=api_key, model=model)
        self.logger = logging.getLogger("PhaseFourCOTAugmentation")
        
    def _execute_pass_1_reasoning(self, section, current_context_question, user_answer, reference_texts):
        """Pass 1: Pure clinical analysis and validation anchoring."""
        system_prompt = """You are a Clinical Psychology Data Architect. Your sole objective is to analyze reference documents against a user's answer to isolate the exact clinical framework and generate a concise validation anchor.

You MUST respond with a valid JSON object containing exactly ONE key: "chain_of_thought".

### Operational Workflow
1. Declare Oracle vs Distractors using format: "CHUNK [X] adalah Oracle. CHUNK [Y, Z, ...] adalah Distractors." (If section is "Opening" or "Ending" and no reference chunks exist, state: "CHUNK N/A adalah Oracle.")
2. Write internal clinical reasoning in Indonesian explaining why the Oracle fits the user's psychological state.
3. Identify the exact unique phrasing the user used in 'USER ANSWER'.
4. At the absolute end of the string, you MUST write exactly: "FRASA VALIDASI VERBATIM: [Tulis klausa pendek di sini]"
   * This clause MUST blend the user's phrasing and the Oracle's concept.
   * It must act as a clinician validating the user (No "saya/aku/ku" referring to the assistant).
   * Keep it under 12 words. Do not include statistics or textbook metrics.
   * Example: "Menyadari bahwa perasaan kosong ini bersifat sementara menunjukkan langkah..."

### Output JSON Schema
{
  "chain_of_thought": "..."
}"""
        user_prompt = f"""SECTION: {section}\nCONTEXT_QUESTION: {current_context_question}\nUSER ANSWER: {user_answer}\n\nRETRIEVED REFERENCE CHUNKS:\n{reference_texts if reference_texts else "N/A"}"""
        
        response = self.gpt_client.run_prompt(system_prompt=system_prompt, user_prompt=user_prompt)
        return self._clean_and_parse_json(response)

    def _execute_pass_2_synthesis(self, section, user_answer, upcoming_base_question, chain_of_thought):
        """Pass 2: Strict verbatim string assembly and upcoming question integration."""
        system_prompt = """You are a Clinical Dialogue Synthesizer. Your sole objective is to take an internal clinical analysis (chain_of_thought) and convert its validation anchor into the final response text.

You MUST respond with a valid JSON object containing exactly ONE key: "assistant_question".

### Operational Workflow
1. Locate the exact text inside "FRASA VALIDASI VERBATIM: [...]" at the end of the provided 'CHAIN OF THOUGHT'.
2. STRIP THE QUOTES: Extract ONLY the text inside the anchor. If the anchor contains single quotes (') or double quotes ("), you MUST strip them out completely. Do not include raw quotation marks inside your final response.

3. EVALUATE TERMINAL STATUS (CRITICAL MECHANISM):
   * [IF SECTION IS "Ending" OR UPCOMING BASE QUESTION IS EMPTY/N/A]: This is the absolute terminal turn of the interview. You are STRICTLY FORBIDDEN from asking any questions, inviting further statements, or using connectors. The final output must consist EXCLUSIVELY of the stripped validation text, modified slightly to read as a natural closing closing statement ending with exactly ONE period (.).
   * [FOR ALL OTHER SECTIONS]: Look at the provided 'UPCOMING BASE QUESTION'. You are completely forbidden from changing its target focus, changing its words, or leaking into other symptom domains. Merge the validation clause and the upcoming question into one cohesive, beautifully flowing compound sentence using a natural conditional connector (e.g., ", dan berkaca dari situasi tersebut, apakah...").

4. BANNED CONNECTOR SYMBOLS: Do not use semicolons (;), dashes (—), or abrupt structural junctions.
5. TOTAL OUTPUT CONSTRAINT: The final output must consist of exactly ONE natural sentence ending with exactly ONE trailing punctuation mark (? or .). No filler, no conversational meta-text.

### Output JSON Schema
{
  "assistant_question": "..."
}"""
        user_prompt = f"""SECTION: {section}\nUSER ANSWER: {user_answer}\nUPCOMING BASE QUESTION: {upcoming_base_question if upcoming_base_question else "N/A"}\n\nCHAIN OF THOUGHT FROM PASS 1:\n{chain_of_thought}"""
        
        response = self.gpt_client.run_prompt(system_prompt=system_prompt, user_prompt=user_prompt)
        return self._clean_and_parse_json(response)


    def _clean_and_parse_json(self, response):
        try:
            TRAILING_COMMA_REGEX = re.compile(r',\s*([\]}])')
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("\n", 1)[0]
            cleaned = cleaned.strip().replace("```json", "").replace("```", "")
            
            cleaned = TRAILING_COMMA_REGEX.sub(r'\1', cleaned)
            
            return json.loads(cleaned)
        except Exception as e:
            self.logger.error(f"JSON parsing error: {e} | Raw: {response}")
            raise

    def generate_raft_cot(self, section, current_context_question, user_answer, upcoming_base_question, reference_texts=None):
        pass1_output = self._execute_pass_1_reasoning(
            section=section,
            current_context_question=current_context_question,
            user_answer=user_answer,
            reference_texts=reference_texts
        )
        cot_string = pass1_output["chain_of_thought"]

        pass2_output = self._execute_pass_2_synthesis(
            section=section,
            user_answer=user_answer,
            upcoming_base_question=upcoming_base_question,
            chain_of_thought=cot_string
        )
        
        return {
            "chain_of_thought": cot_string,
            "assistant_question": pass2_output["assistant_question"]
        }

    def run(self, phase3_dialogs):
        augmented_dialogs = []
        
        for dialog in phase3_dialogs:
            dialog_id = dialog.get("dialog_id")
            self.logger.info(f"Augmenting dialog_id={dialog_id} with Two-Pass Phase 4 Pipeline")
            augmented_messages = []
            running_response = None
            messages = dialog.get("messages", [])
            
            for idx, msg in enumerate(messages):
                msg_type = msg.get("type")
                user_content = msg.get("user_content", "")

                if idx == 0 or running_response is None:
                    current_context_question = msg.get("assistant_content", "")
                    if not current_context_question:
                        current_context_question = msg.get("current_assistant_response", "")
                else:
                    current_context_question = running_response

                if idx + 1 < len(messages):
                    upcoming_base_question = messages[idx + 1].get("assistant_content", "")
                    if not upcoming_base_question:
                        upcoming_base_question = messages[idx + 1].get("current_assistant_response", "")
                else:
                    upcoming_base_question = ""

                formatted_refs = ""
                if msg_type == "Survey":
                    documents = msg.get("set_of_documents", [])
                    for doc in documents:
                        formatted_refs += f"--- CHUNK {doc['rank']} (Similarity Score: {doc['score']:.4f}) ---\n{doc['chunk']}\n\n"

                try:
                    raft_output = self.generate_raft_cot(
                        section=msg.get("section", msg_type),
                        current_context_question=current_context_question,
                        user_answer=user_content,
                        upcoming_base_question=upcoming_base_question,
                        reference_texts=formatted_refs if msg_type == "Survey" else None
                    )

                    out_msg = {
                        "type": msg_type,
                        "chain_of_thought": raft_output["chain_of_thought"],
                        "current_assistant_response": current_context_question,
                        "user_content": user_content,
                        "following_assistant_response": raft_output["assistant_question"]
                    }
                    
                    if msg_type == "Survey":
                        out_msg["section"] = msg.get("section")
                        out_msg["scoring_system"] = msg.get("scoring_system", [])
                        out_msg["grouped_questions_score"] = msg.get("grouped_questions_score", [])
                        out_msg["set_of_documents"] = msg.get("set_of_documents", [])

                    augmented_messages.append(out_msg)
                    running_response = raft_output["assistant_question"]

                except Exception as e:
                    self.logger.error(f"Generation failed at node index {idx}: {e}")
                    
                    fallback_msg = {
                        "type": msg_type,
                        "chain_of_thought": "FALLBACK: Clinical reasoning parsing failed.",
                        "current_assistant_response": current_context_question,
                        "user_content": user_content,
                        "following_assistant_response": upcoming_base_question if upcoming_base_question else "Terima kasih."
                    }
                    if msg_type == "Survey":
                        fallback_msg["section"] = msg.get("section")
                        fallback_msg["scoring_system"] = msg.get("scoring_system", [])
                        fallback_msg["grouped_questions_score"] = msg.get("grouped_questions_score", [])
                        fallback_msg["set_of_documents"] = msg.get("set_of_documents", [])
                        
                    augmented_messages.append(fallback_msg)
                    running_response = fallback_msg["following_assistant_response"]

            augmented_dialogs.append({
                "dialog_id": dialog_id,
                "name": dialog.get("name"),
                "messages": augmented_messages
            })

        return augmented_dialogs