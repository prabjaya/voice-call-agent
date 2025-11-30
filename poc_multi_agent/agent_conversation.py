"""
Multi-Agent Conversational LLM
Based on agent_config.py - Supports PIZZA, LOGISTICS, and more
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agent_config import AGENT_METADATA
from dotenv import load_dotenv
import os
import json

load_dotenv()


class LLMOutput(BaseModel):
    """Structured output from LLM"""
    response_type: Literal['THANK_YOU_RESPONSE', 'HANDOVER_TO_HUMAN', 'NEED_MORE_INFO']
    
    # LOGISTICS fields
    charge: Optional[str] = None
    availability_time: Optional[str] = None
    
    # PIZZA fields
    pizza_type: Optional[str] = None
    size: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_time: Optional[str] = None
    
    feedback: str


class AgentConversation:
    """Manages conversation for different agent types"""
    
    def __init__(self, agent_type: str = "LOGISTICS", language: str = "English"):
        if agent_type not in AGENT_METADATA:
            raise ValueError(f"Invalid agent_type. Choose from: {list(AGENT_METADATA.keys())}")
        
        self.agent_type = agent_type
        self.language = language
        self.agent_config = AGENT_METADATA[agent_type]
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7
        )
        
        self.conversation_history = []
        self.collected_data = {}
        
        # Build system prompt from agent config
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt based on agent type"""
        
        base_prompt = self.agent_config["system_prompt"]
        
        # Add conversational instructions
        conversational_prompt = f"""
{base_prompt}

CONVERSATION STYLE:
- Be natural, friendly, and conversational
- Adapt to user's responses
- Handle questions, greetings, confusion naturally
- Guide conversation to collect required information
- Be patient and understanding
- If user wants human, transfer them

RESPONSE FORMAT (JSON):
{{
  "response_type": "THANK_YOU_RESPONSE" | "NEED_MORE_INFO" | "HANDOVER_TO_HUMAN",
"""
        
        # Add fields based on agent type
        if self.agent_type == "LOGISTICS":
            conversational_prompt += """
  "charge": "extracted charge or null",
  "availability_time": "extracted time or null",
"""
        elif self.agent_type == "PIZZA":
            conversational_prompt += """
  "pizza_type": "extracted pizza type or null",
  "size": "extracted size or null",
  "delivery_address": "extracted address or null",
  "delivery_time": "extracted delivery time or null",
"""
        
        conversational_prompt += """
  "feedback": "Your natural conversational response"
}

CRITICAL RULES:
1. ALWAYS return ONLY valid JSON - no extra text before or after
2. When you have ALL required information → response_type = "THANK_YOU_RESPONSE"
3. When missing information → response_type = "NEED_MORE_INFO", ask naturally
4. When user wants human → response_type = "HANDOVER_TO_HUMAN"
5. If user is confused, explain clearly in feedback

IMPORTANT: Your entire response must be ONLY the JSON object, nothing else!"""
        
        return conversational_prompt
    
    def start_conversation(self):
        """Start the conversation"""
        print("=" * 70)
        print(f"🤖 {self.agent_type} AGENT - Conversational AI")
        print("=" * 70)
        print()
        print(f"Agent Type: {self.agent_type}")
        print(f"Language: {self.language}")
        print()
        print("Type 'quit' to exit anytime.")
        print()
        print("=" * 70)
        print()
        
        # Get welcome message from config
        welcome_msg = self.agent_config["welcome_msg"].get(self.language, "")
        print(f"🤖 AI: {welcome_msg}")
        print()
        
        # Add to history
        self.conversation_history.append({
            "role": "assistant",
            "content": welcome_msg
        })
    
    def process_user_input(self, user_input: str) -> LLMOutput:
        """Process user input and get AI response"""
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Build messages for LLM
        messages = [SystemMessage(content=self.system_prompt)]
        
        # Add conversation history
        for msg in self.conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current collected data context
        context = f"\nCurrent collected data: {json.dumps(self.collected_data)}"
        messages.append(HumanMessage(content=context))
        
        # Call LLM
        response = self.llm.invoke(messages)
        
        # Parse JSON response
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()
        
        # Try to find JSON in the response
        try:
            # Try direct parsing
            result_dict = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result_dict = json.loads(json_match.group())
            else:
                # Fallback: Create a default response
                result_dict = {
                    "response_type": "NEED_MORE_INFO",
                    "charge": None,
                    "availability_time": None,
                    "feedback": content if content else "Could you please provide the shipment charge and availability time?"
                }
        
        llm_output = LLMOutput(**result_dict)
        
        # Update collected data based on agent type
        if self.agent_type == "LOGISTICS":
            if llm_output.charge:
                self.collected_data["charge"] = llm_output.charge
            if llm_output.availability_time:
                self.collected_data["availability_time"] = llm_output.availability_time
        
        elif self.agent_type == "PIZZA":
            if llm_output.pizza_type:
                self.collected_data["pizza_type"] = llm_output.pizza_type
            if llm_output.size:
                self.collected_data["size"] = llm_output.size
            if llm_output.delivery_address:
                self.collected_data["delivery_address"] = llm_output.delivery_address
            if llm_output.delivery_time:
                self.collected_data["delivery_time"] = llm_output.delivery_time
        
        # Add AI response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": llm_output.feedback
        })
        
        return llm_output
    
    def display_collected_data(self):
        """Display collected data"""
        if self.collected_data:
            print("📊 Collected Data:")
            for key, value in self.collected_data.items():
                emoji = "💰" if "charge" in key else "⏰" if "time" in key else "🍕" if "pizza" in key else "📦"
                print(f"   {emoji} {key.replace('_', ' ').title()}: {value}")
            print()
    
    def run_conversation(self):
        """Run the full conversation"""
        
        self.start_conversation()
        
        while True:
            # Get user input
            user_input = input("👤 You: ").strip()
            print()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            try:
                # Process with LLM
                result = self.process_user_input(user_input)
                
                # Display AI response
                print(f"🤖 AI: {result.feedback}")
                print()
                
                # Show collected data (if any)
                if self.collected_data:
                    self.display_collected_data()
                
                # Check if conversation is complete
                if result.response_type == "THANK_YOU_RESPONSE":
                    print("✅ Conversation Complete!")
                    print()
                    
                    # Get thank you message from config
                    thank_you_msg = self.agent_config["positive_thank_you_msg"]
                    print(f"🎉 {thank_you_msg}")
                    print()
                    
                    # Build final response with all fields
                    final_response = {
                        "response_type": result.response_type,
                        "feedback": result.feedback
                    }
                    
                    # Add agent-specific fields
                    if self.agent_type == "LOGISTICS":
                        final_response["charge"] = result.charge
                        final_response["availability_time"] = result.availability_time
                    elif self.agent_type == "PIZZA":
                        final_response["pizza_type"] = result.pizza_type
                        final_response["size"] = result.size
                        final_response["delivery_address"] = result.delivery_address
                        final_response["delivery_time"] = result.delivery_time
                    
                    print("📄 Final Response (JSON):")
                    print(json.dumps(final_response, indent=2))
                    print()
                    break
                
                elif result.response_type == "HANDOVER_TO_HUMAN":
                    print("📞 Transferring to human agent...")
                    
                    # Get negative message from config
                    negative_msg = self.agent_config["negative_thank_you_msg"]
                    print(f"💬 {negative_msg}")
                    break
                
                print("-" * 70)
                print()
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                print("Let's try again...")
                print()


def main():
    """Main function"""
    print()
    print("🎯 Multi-Agent Conversational AI")
    print()
    
    # Select agent type
    print("Available Agents:")
    for i, agent_type in enumerate(AGENT_METADATA.keys(), 1):
        print(f"  {i}. {agent_type}")
    print()
    
    choice = input("Select agent (1, 2, etc.) or press Enter for LOGISTICS: ").strip()
    
    # Map choice to agent type
    agent_types = list(AGENT_METADATA.keys())
    if choice.isdigit() and 1 <= int(choice) <= len(agent_types):
        agent_type = agent_types[int(choice) - 1]
    else:
        agent_type = "LOGISTICS"
    
    print()
    print(f"Selected: {agent_type}")
    print()
    
    # Start conversation
    conversation = AgentConversation(agent_type=agent_type, language="English")
    conversation.run_conversation()
    
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
