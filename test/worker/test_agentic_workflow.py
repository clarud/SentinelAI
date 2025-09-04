#!/usr/bin/env python3
"""
Test the new agentic orchestrator workflow with real documents.
"""
import sys
import os

# Add project root to sys.path
current_file = os.path.abspath(__file__)
project_root = current_file
while True:
    project_root = os.path.dirname(project_root)
    if os.path.isdir(os.path.join(project_root, 'services')):
        break

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.worker.worker.agents.orchestrator import assess_document

def test_suspicious_email():
    """Test with a suspicious email to see agentic routing."""
    print("🧪 Testing Agentic Workflow with Suspicious Email")
    print("=" * 60)
    
    suspicious_email = {
        'subject': 'URGENT: Verify Your Account NOW or Face Suspension',
        'from': 'security@amazon-verification.com',
        'to': 'customer@example.com',
        'body': '''Dear Customer,
        
We have detected unusual activity on your Amazon account. To prevent 
unauthorized access, we need you to verify your identity immediately.

Click here to verify: http://amazon-verify.suspicious-domain.ru/login

WARNING: Failure to verify within 24 hours will result in permanent 
account suspension and loss of all order history.

Please provide:
- Full Name
- Credit Card Number  
- Social Security Number
- Bank Account Details

This is an automated message from Amazon Security Team.''',
        'date': '2025-09-04 10:00:00'
    }
    
    print(f"Document: {suspicious_email['subject']} from {suspicious_email['from']}")
    print(f"Body preview: {suspicious_email['body'][:200]}...")
    print("\n🤖 Running agentic workflow...")
    
    result = assess_document(suspicious_email)
    
    print("\n📊 AGENTIC WORKFLOW RESULTS:")
    print("=" * 40)
    print(f"Output: {result}")
    print(f"Classification: {result.get('is_scam', 'unknown')}")
    print(f"Confidence: {result.get('confidence_level', 0):.2f}")
    print(f"Scam Probability: {result.get('scam_probability', 0):.1f}%")
    print(f"Explanation: {result.get('explanation', 'No explanation')[:200]}...")
    
    metadata = result.get('processing_metadata', {})
    print(f"\n⚡ ROUTER DECISION:")
    print(f"Route Taken: {metadata.get('router_route', 'unknown')}")
    print(f"Agents Called: {metadata.get('agents_called', [])}")
    print(f"Total Time: {metadata.get('total_time', 0):.2f}s")
    print(f"Evidence Gathered: {metadata.get('evidence_gathered', 0)}")
    print(f"Workflow ID: {metadata.get('workflow_id', 'unknown')}")
    
    return result

def test_legitimate_email():
    """Test with a legitimate email to see different routing."""
    print("\n🧪 Testing Agentic Workflow with Legitimate Email")
    print("=" * 60)
    
    legitimate_email = {
        'subject': 'Your GitHub security alert',
        'from': 'noreply@github.com',
        'to': 'developer@example.com',
        'body': '''Hello,

We're writing to let you know that a new personal access token was 
created for your account.

Token name: VSCode-Integration
Created: September 4, 2025 at 5:20 PM UTC

If you created this token, you can ignore this email. If you did not 
create this token, please review your account security settings.

Best regards,
The GitHub Team''',
        'date': '2025-09-04 17:20:00'
    }
    
    print(f"Document: {legitimate_email['subject']} from {legitimate_email['from']}")
    print(f"Body preview: {legitimate_email['body'][:200]}...")
    print("\n🤖 Running agentic workflow...")
    
    result = assess_document(legitimate_email)
    
    print("\n📊 AGENTIC WORKFLOW RESULTS:")
    print("=" * 40)
    print(f"Output: {result}")
    print(f"Classification: {result.get('is_scam', 'unknown')}")
    print(f"Confidence: {result.get('confidence_level', 0):.2f}")
    print(f"Scam Probability: {result.get('scam_probability', 0):.1f}%")
    print(f"Explanation: {result.get('explanation', 'No explanation')[:200]}...")
    
    metadata = result.get('processing_metadata', {})
    print(f"\n⚡ ROUTER DECISION:")
    print(f"Route Taken: {metadata.get('router_route', 'unknown')}")
    print(f"Agents Called: {metadata.get('agents_called', [])}")
    print(f"Total Time: {metadata.get('total_time', 0):.2f}s")
    print(f"Evidence Gathered: {metadata.get('evidence_gathered', 0)}")
    print(f"Workflow ID: {metadata.get('workflow_id', 'unknown')}")
    
    return result

if __name__ == "__main__":
    print("🚀 AGENTIC ORCHESTRATOR TEST")
    print("Testing the new ROUTER-based dynamic workflow")
    print("=" * 60)
    
    try:
        # Test 1: Suspicious email (should trigger different route than legitimate)
        result1 = test_suspicious_email()
        
        # Test 2: Legitimate email (should trigger different route)
        result2 = test_legitimate_email()
        
        print("\n🎯 COMPARISON OF ROUTER DECISIONS:")
        print("=" * 50)
        print(f"Suspicious Email Route: {result1.get('processing_metadata', {}).get('router_route', 'unknown')}")
        print(f"Legitimate Email Route: {result2.get('processing_metadata', {}).get('router_route', 'unknown')}")
        
        print(f"\nSuspicious Agents: {result1.get('processing_metadata', {}).get('agents_called', [])}")
        print(f"Legitimate Agents: {result2.get('processing_metadata', {}).get('agents_called', [])}")
        
        print("\n✅ Agentic workflow test completed!")
        print("📝 Check the assessment logs for detailed decision tracking.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
