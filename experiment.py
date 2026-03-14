import docx

def create_test_doc():
    doc = docx.Document()
    
    # The exact lines of the Stress Test SOP
    steps = [
        "1. Receive fraud alert from the monitoring system.",
        "2. Lock the customer account temporarily.",
        "3. Review the flagged transaction details.",
        "3.1 If the transaction matches known fraud patterns, go to step 5.",
        "3.2 If the transaction is ambiguous, contact the customer.",
        "3.2.1 If the customer confirms the charge is legitimate, go to step 6.",
        "3.2.2 If the customer denies the charge, initiate a chargeback with the merchant.",
        "3.2.3 If the customer does not answer the phone, go back to step 3.2.",
        "4. Issue a provisional credit to the customer account.",
        "5. Issue a new physical credit card to the customer.",
        "6. Close the fraud investigation ticket."
    ]
    
    for step in steps:
        doc.add_paragraph(step)
        
    doc.save('stress_test.docx')
    print("✅ Successfully created 'stress_test.docx'!")

if __name__ == "__main__":
    create_test_doc()