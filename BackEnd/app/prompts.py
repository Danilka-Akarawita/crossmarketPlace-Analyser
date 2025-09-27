RECOMMENDATION_PROMPT = """
            Based on the following user constraints and available products, provide recommendations:
            
            User Constraints: {constraints}
            Available Products: {products}
            
            Please recommend up to 3 products with clear rationales. For each recommendation:
            1. Explain why it matches the user's needs
            2. Highlight key specifications that meet requirements
            3. Mention any trade-offs or considerations
            
            Use output format as :{format_instructions}
            """
QA_PROMPT = """
            Context about laptops: {context}
            
            Question: {question}
            
            Please provide a helpful answer based on the context. If the information isn't available, say so.
            Include specific citations from the context when possible.
            
            Use output format as :{format_instructions}            """
