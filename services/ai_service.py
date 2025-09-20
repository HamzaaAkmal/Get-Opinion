"""
AI Service for query generation and processing
Handles Gemini AI integration and query variations
"""
import google.generativeai as genai
from config import Config


class AIService:
    """Service for AI-powered query generation and processing"""
    
    def __init__(self):
        self.config = Config()
        if self.config.GEMINI_API_KEY:
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            print("⚠️  Gemini API key not configured - AI features will be disabled")
    
    def is_available(self):
        """Check if AI service is available"""
        return self.model is not None
    
    def generate_query_variations(self, original_query, num_variations=None):
        """Generate multiple variations of a query using Gemini AI"""
        if not self.is_available():
            print("❌ AI service not available - returning original query only")
            return [original_query]
        
        if num_variations is None:
            num_variations = self.config.NUM_QUERY_VARIATIONS
        
        try:
            print(f"🤖 Generating {num_variations} query variations using Gemini AI...")

            prompt = f"""
            Generate {num_variations} different variations of this search query: "{original_query}"

            Requirements:
            - Each variation should have different wording and style
            - Keep the core meaning the same but vary the phrasing
            - Make them suitable for YouTube and Reddit search
            - Include different perspectives, synonyms, and rephrasings
            - Some should be more formal, some more casual
            - Some should be questions, some statements
            - Return only the variations as a numbered list, one per line
            - Do not include any explanations or additional text

            Example format:
            1. First variation here
            2. Second variation here
            ...
            """

            response = self.model.generate_content(prompt)
            variations_text = response.text.strip()

            # Parse the variations from the response
            variations = []
            for line in variations_text.split('\n'):
                line = line.strip()
                if line and any(char.isdigit() for char in line[:3]):  # Check if line starts with number
                    # Remove numbering (e.g., "1. ", "2. ", etc.)
                    variation = line.split('.', 1)[-1].strip()
                    if variation:
                        variations.append(variation)

            # Ensure we have at least some variations
            if not variations:
                print("❌ No variations generated, using original query")
                return [original_query]

            # Limit to requested number
            variations = variations[:num_variations]

            print(f"✅ Generated {len(variations)} query variations:")
            for i, var in enumerate(variations[:5], 1):  # Show first 5
                print(f"   {i}. {var}")
            if len(variations) > 5:
                print(f"   ... and {len(variations) - 5} more")

            return variations

        except Exception as e:
            print(f"❌ Error generating query variations: {e}")
            print("💡 Falling back to original query")
            return [original_query]
    
    def analyze_query_relevance(self, query, comment_text):
        """Analyze if a comment is relevant to a query using AI"""
        if not self.is_available():
            # Fallback to simple keyword matching
            query_terms = set(query.lower().split())
            comment_lower = comment_text.lower()
            return any(term in comment_lower for term in query_terms)
        
        try:
            prompt = f"""
            Analyze if this comment is relevant to the search query.
            
            Query: "{query}"
            Comment: "{comment_text[:500]}..."
            
            Reply with only "YES" if relevant or "NO" if not relevant.
            """
            
            response = self.model.generate_content(prompt)
            result = response.text.strip().upper()
            
            return result == "YES"
            
        except Exception as e:
            print(f"❌ Error analyzing relevance: {e}")
            # Fallback to keyword matching
            query_terms = set(query.lower().split())
            comment_lower = comment_text.lower()
            return any(term in comment_lower for term in query_terms)
    
    def suggest_related_queries(self, original_query, num_suggestions=5):
        """Suggest related queries for broader search"""
        if not self.is_available():
            print("❌ AI service not available - cannot suggest related queries")
            return []
        
        try:
            prompt = f"""
            Based on this search query: "{original_query}"
            
            Suggest {num_suggestions} related but different search queries that might find additional relevant content.
            These should explore different angles, related topics, or alternative ways to find similar information.
            
            Return only the suggested queries as a numbered list, one per line.
            
            Example format:
            1. First suggestion here
            2. Second suggestion here
            ...
            """
            
            response = self.model.generate_content(prompt)
            suggestions_text = response.text.strip()
            
            suggestions = []
            for line in suggestions_text.split('\n'):
                line = line.strip()
                if line and any(char.isdigit() for char in line[:3]):
                    suggestion = line.split('.', 1)[-1].strip()
                    if suggestion:
                        suggestions.append(suggestion)
            
            return suggestions[:num_suggestions]
            
        except Exception as e:
            print(f"❌ Error suggesting related queries: {e}")
            return []
    
    def summarize_comments(self, comments, max_length=500):
        """Generate a summary of comments using AI"""
        if not self.is_available():
            print("❌ AI service not available - cannot summarize comments")
            return "AI summarization not available"
        
        try:
            # Combine comment texts for analysis
            combined_text = "\n".join([comment.get('text', '')[:200] for comment in comments[:50]])
            
            prompt = f"""
            Analyze and summarize the main themes, sentiments, and key points from these comments:
            
            {combined_text[:3000]}...
            
            Provide a concise summary highlighting:
            1. Main topics discussed
            2. Overall sentiment
            3. Key concerns or interests
            4. Notable patterns or trends
            
            Keep the summary under {max_length} characters.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"❌ Error summarizing comments: {e}")
            return f"Error generating summary: {str(e)}"


# Global AI service instance
ai_service = AIService()