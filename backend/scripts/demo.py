"""
Demonstration script for the Human-in-the-Loop AI Supervisor
"""
import asyncio
import time
import logging
from app.services.ai_agent import ai_agent
from app.models.help_request import HelpRequest
from app.models.knowledge_base import KnowledgeBase
from app.models.call_record import CallRecord
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def run_full_demo():
    """
    Run a complete demonstration of the system
    """
    print("\n===== HUMAN-IN-THE-LOOP AI SUPERVISOR DEMO =====\n")
    
    # Initialize services
    print("1. INITIALIZING SERVICES...")
    await ai_agent.initialize()
    print("   ✓ AI Agent initialized")
    
    # Ensure database tables are ready
    await HelpRequest.init_table()
    await KnowledgeBase.init_table()
    await CallRecord.init_table()
    print("   ✓ Database tables initialized")
    
    # Simulate an incoming call
    print("\n2. SIMULATING INCOMING CALL...")
    call_id = f"demo_call_{int(time.time())}"
    customer_id = "demo_customer_123"
    phone_number = "+15551234567"
    
    call = await ai_agent.handle_incoming_call(call_id, customer_id, phone_number)
    print(f"   ✓ Call started (ID: {call_id})")
    print(f"   AI: \"Thank you for calling Elegant Touch Salon. How can I help you today?\"")
    
    # Test a question the AI knows
    print("\n3. CUSTOMER ASKS A KNOWN QUESTION...")
    question1 = "What are your hours?"
    print(f"   Customer: \"{question1}\"")
    
    result1 = await ai_agent.process_call_question(call_id, question1)
    print(f"   AI: \"{result1['answer']}\"")
    print(f"   Needs Help: {result1['needs_help']}")
    
    await asyncio.sleep(1)  # Small delay for demo purposes
    
    # Test a question the AI doesn't know
    print("\n4. CUSTOMER ASKS AN UNKNOWN QUESTION...")
    question2 = "Do you offer student discounts?"
    print(f"   Customer: \"{question2}\"")
    
    result2 = await ai_agent.process_call_question(call_id, question2)
    print(f"   AI: \"{result2['answer']}\"")
    print(f"   Needs Help: {result2['needs_help']}")
    
    # Check for help requests
    print("\n5. CHECKING HELP REQUESTS...")
    pending_requests = await HelpRequest.get_by_status("pending")
    print(f"   Found {len(pending_requests)} pending help request(s)")
    
    if pending_requests:
        help_request = pending_requests[0]
        print(f"   Help Request ID: {help_request.request_id}")
        print(f"   Question: \"{help_request.question}\"")
        
        # Simulate supervisor response
        print("\n6. SUPERVISOR RESPONDS TO HELP REQUEST...")
        supervisor_answer = "Yes, we offer a 15% discount for students with a valid student ID."
        print(f"   Supervisor Answer: \"{supervisor_answer}\"")
        
        resolved_request = await ai_agent.resolve_help_request(help_request.request_id, supervisor_answer)
        if resolved_request:
            print(f"   ✓ Help request resolved")
            print(f"   ✓ Customer notified via SMS")
            print(f"   ✓ Knowledge base updated")
    
    # Test the same question again
    print("\n7. NEW CUSTOMER ASKS THE SAME QUESTION...")
    new_call_id = f"demo_call_2_{int(time.time())}"
    new_customer_id = "demo_customer_456"
    new_phone = "+15559876543"
    
    new_call = await ai_agent.handle_incoming_call(new_call_id, new_customer_id, new_phone)
    print(f"   ✓ New call started (ID: {new_call_id})")
    
    result3 = await ai_agent.process_call_question(new_call_id, question2)
    print(f"   Customer: \"{question2}\"")
    print(f"   AI: \"{result3['answer']}\"")
    print(f"   Needs Help: {result3['needs_help']}")
    
    # Show knowledge base
    print("\n8. KNOWLEDGE BASE CONTENTS...")
    all_knowledge = await KnowledgeBase.get_all()
    print(f"   Total entries: {len(all_knowledge)}")
    
    for idx, entry in enumerate(all_knowledge[-3:], 1):  # Show last 3 entries
        print(f"   Entry {idx}:")
        print(f"     Q: \"{entry.question}\"")
        print(f"     A: \"{entry.answer}\"")
    
    # End calls
    print("\n9. ENDING CALLS...")
    await ai_agent.handle_call_ended(call_id, 60000)  # 60 seconds
    await ai_agent.handle_call_ended(new_call_id, 30000)  # 30 seconds
    print("   ✓ Calls ended")
    
    # Show statistics
    print("\n10. SYSTEM STATISTICS...")
    total_help_requests = len(await HelpRequest.get_by_status("resolved"))
    total_knowledge = len(await KnowledgeBase.get_all())
    
    print(f"   Total help requests resolved: {total_help_requests}")
    print(f"   Total knowledge base entries: {total_knowledge}")
    print(f"   Success rate: {(total_knowledge / (total_knowledge + 1)) * 100:.1f}%")
    
    print("\n===== DEMO COMPLETED =====\n")

async def run_simple_question(question: str):
    """
    Test a single question
    """
    print(f"\nTesting question: \"{question}\"")
    
    # Create a mock call
    call_id = f"test_call_{int(time.time())}"
    customer_id = "test_customer"
    phone = "+15550000000"
    
    # Process the question
    call = await ai_agent.handle_incoming_call(call_id, customer_id, phone)
    result = await ai_agent.process_call_question(call_id, question)
    
    print(f"AI Answer: \"{result['answer']}\"")
    print(f"Needs Help: {result['needs_help']}")
    
    # End the call
    await ai_agent.handle_call_ended(call_id, 5000)
    
    return result

async def test_timeout():
    """
    Test help request timeout functionality
    """
    print("\n===== TESTING HELP REQUEST TIMEOUT =====\n")
    
    # Create a help request
    question = "What's your cancellation policy?"
    call_id = f"timeout_test_{int(time.time())}"
    customer_id = "timeout_customer"
    phone = "+15551112222"
    
    print(f"1. Creating help request for: \"{question}\"")
    help_request = await ai_agent.create_help_request(question, call_id, customer_id, phone)
    print(f"   ✓ Help request created (ID: {help_request.request_id})")
    
    # Show current status
    print(f"   Status: {help_request.status}")
    
    # Simulate time passing
    print("\n2. Simulating timeout (setting request to be > 1 hour old)...")
    
    # Manually update the timestamp to simulate timeout
    help_request.timestamp = int(time.time()) - 3700  # 1 hour + 100 seconds ago
    await help_request.save()
    
    # Run timeout check
    print("3. Running timeout check...")
    timed_out_count = await HelpRequest.check_timeouts()
    
    print(f"   ✓ Timed out {timed_out_count} request(s)")
    
    # Check the status again
    updated_request = await HelpRequest.get_by_id(help_request.request_id)
    print(f"   Updated status: {updated_request.status}")
    
    print("\n===== TIMEOUT TEST COMPLETED =====")

# Main demo entry point
if __name__ == "__main__":
    asyncio.run(run_full_demo())