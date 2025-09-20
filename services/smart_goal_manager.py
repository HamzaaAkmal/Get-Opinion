"""
Smart Goal-Oriented Manager
Automatically adapts strategies to fulfill user targets in any way possible
Makes intelligent decisions about retry attempts, sources, query variations, and escalation
"""
import math
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
from services.ai_service import ai_service


class SmartGoalManager:
    """Intelligent goal management system that adapts to fulfill targets"""
    
    def __init__(self):
        self.goal_tracking = {
            'target_comments': 0,
            'achieved_comments': 0,
            'progress_percentage': 0,
            'attempts_made': 0,
            'success_rate': 0,
            'query_effectiveness': {},
            'source_performance': {'youtube': 0, 'reddit': 0},
            'escalation_level': 0
        }
        
        # Smart adaptation thresholds
        self.escalation_thresholds = [25, 50, 75, 90]  # Progress percentages for escalation
        self.max_escalation_level = 4
        
    def analyze_goal_status(self, target: int, achieved: int, queries_processed: int, 
                          total_queries: int, source_stats: Dict) -> Dict[str, Any]:
        """Analyze current progress and determine smart adaptations needed"""
        
        progress = (achieved / target * 100) if target > 0 else 0
        completion_rate = (queries_processed / total_queries * 100) if total_queries > 0 else 0
        
        # Update tracking
        self.goal_tracking.update({
            'target_comments': target,
            'achieved_comments': achieved,
            'progress_percentage': progress,
            'attempts_made': queries_processed,
            'success_rate': completion_rate
        })
        
        # Determine escalation level based on progress vs completion
        escalation_needed = self._calculate_escalation_level(progress, completion_rate)
        
        # Generate smart recommendations
        recommendations = self._generate_smart_recommendations(
            target, achieved, progress, completion_rate, source_stats
        )
        
        return {
            'current_progress': progress,
            'completion_rate': completion_rate,
            'escalation_level': escalation_needed,
            'recommendations': recommendations,
            'goal_status': self._determine_goal_status(progress, completion_rate),
            'adaptive_strategy': self._get_adaptive_strategy(escalation_needed)
        }
    
    def _calculate_escalation_level(self, progress: float, completion_rate: float) -> int:
        """Calculate appropriate escalation level based on progress vs completion"""
        
        # If we're far into the queries but haven't achieved the target, escalate
        if completion_rate > 70 and progress < 50:
            return 3  # High escalation
        elif completion_rate > 50 and progress < 30:
            return 2  # Medium escalation
        elif completion_rate > 30 and progress < 20:
            return 1  # Low escalation
        else:
            return 0  # No escalation needed
    
    def _determine_goal_status(self, progress: float, completion_rate: float) -> str:
        """Determine the current goal achievement status"""
        
        if progress >= 100:
            return "TARGET_ACHIEVED"
        elif progress >= 80:
            return "NEARLY_COMPLETE"
        elif progress >= 50:
            return "GOOD_PROGRESS"
        elif progress >= 25:
            return "MODERATE_PROGRESS"
        elif completion_rate > 50 and progress < 25:
            return "UNDERPERFORMING"
        else:
            return "EARLY_STAGE"
    
    def _generate_smart_recommendations(self, target: int, achieved: int, 
                                      progress: float, completion_rate: float,
                                      source_stats: Dict) -> List[str]:
        """Generate intelligent recommendations to improve goal achievement"""
        
        recommendations = []
        
        # Progress-based recommendations
        if progress < 25 and completion_rate > 40:
            recommendations.append("🔄 Increase retry attempts per query")
            recommendations.append("📈 Generate more query variations")
            recommendations.append("⏰ Extend timeout periods")
        
        if progress < 50 and completion_rate > 60:
            recommendations.append("🚀 Enable aggressive escalation mode")
            recommendations.append("🔀 Use all available API keys simultaneously")
            recommendations.append("🎯 Focus on high-performing sources")
        
        # Source performance recommendations
        youtube_performance = source_stats.get('youtube', {}).get('avg_comments', 0)
        reddit_performance = source_stats.get('reddit', {}).get('avg_comments', 0)
        
        if youtube_performance > reddit_performance * 2:
            recommendations.append("📺 Prioritize YouTube sources (higher yield)")
        elif reddit_performance > youtube_performance * 2:
            recommendations.append("🔶 Prioritize Reddit sources (higher yield)")
        else:
            recommendations.append("⚖️ Maintain balanced source strategy")
        
        # Target-based scaling recommendations
        if target > 10000:
            recommendations.append("🎯 Enable large-scale processing mode")
        if target > 50000:
            recommendations.append("⚡ Activate maximum parallelization")
        
        return recommendations
    
    def _get_adaptive_strategy(self, escalation_level: int) -> Dict[str, Any]:
        """Get adaptive strategy based on escalation level"""
        
        strategies = {
            0: {  # Normal operation
                'max_retries': 1,
                'timeout_multiplier': 1.0,
                'query_variations_multiplier': 1.0,
                'parallel_workers': 4,
                'comments_per_video': 80,
                'reddit_comments_limit': 1500
            },
            1: {  # Low escalation
                'max_retries': 2,
                'timeout_multiplier': 1.2,
                'query_variations_multiplier': 1.5,
                'parallel_workers': 6,
                'comments_per_video': 100,
                'reddit_comments_limit': 2000
            },
            2: {  # Medium escalation
                'max_retries': 3,
                'timeout_multiplier': 1.5,
                'query_variations_multiplier': 2.0,
                'parallel_workers': 8,
                'comments_per_video': 120,
                'reddit_comments_limit': 2500
            },
            3: {  # High escalation
                'max_retries': 4,
                'timeout_multiplier': 2.0,
                'query_variations_multiplier': 2.5,
                'parallel_workers': 10,
                'comments_per_video': 150,
                'reddit_comments_limit': 3000
            }
        }
        
        return strategies.get(escalation_level, strategies[0])
    
    def calculate_smart_query_distribution(self, total_queries: int, target_comments: int,
                                         estimated_comments_per_query: int = 500) -> Dict[str, int]:
        """Calculate intelligent query distribution to achieve target"""
        
        # Calculate how many comments we need per query to reach target
        comments_per_query_needed = math.ceil(target_comments / total_queries)
        
        # Adjust based on historical performance
        if comments_per_query_needed > estimated_comments_per_query * 2:
            # We need to be more aggressive
            suggested_queries = math.ceil(target_comments / estimated_comments_per_query)
            return {
                'recommended_total_queries': min(suggested_queries, total_queries * 2),
                'comments_per_query_target': estimated_comments_per_query,
                'aggressive_mode': True,
                'strategy': 'SCALE_UP_QUERIES'
            }
        elif comments_per_query_needed < estimated_comments_per_query * 0.5:
            # We can be more conservative
            return {
                'recommended_total_queries': total_queries,
                'comments_per_query_target': comments_per_query_needed,
                'aggressive_mode': False,
                'strategy': 'CONSERVATIVE'
            }
        else:
            # Balanced approach
            return {
                'recommended_total_queries': total_queries,
                'comments_per_query_target': comments_per_query_needed,
                'aggressive_mode': False,
                'strategy': 'BALANCED'
            }
    
    def generate_emergency_queries(self, original_query: str, deficit: int, 
                                 successful_patterns: List[str] = None) -> List[str]:
        """Generate emergency queries when target is not being met"""
        
        try:
            # Build prompt for emergency query generation
            prompt = f"""
            EMERGENCY: We need {deficit} more comments to reach our target.
            Original query: "{original_query}"
            
            Generate 10 high-yield query variations that are likely to get many comments.
            Focus on:
            1. Controversial or discussion-heavy topics related to the original query
            2. Questions that encourage responses
            3. Popular trends or current events related to the topic
            4. Broader related topics that might have more content
            
            Successful patterns so far: {successful_patterns if successful_patterns else 'None identified'}
            
            Return only the queries, one per line.
            """
            
            emergency_queries = ai_service.generate_query_variations(original_query, 10, custom_prompt=prompt)
            
            return emergency_queries if emergency_queries else self._fallback_emergency_queries(original_query)
            
        except Exception as e:
            print(f"⚠️ AI emergency query generation failed: {e}")
            return self._fallback_emergency_queries(original_query)
    
    def _fallback_emergency_queries(self, original_query: str) -> List[str]:
        """Fallback emergency queries when AI fails"""
        
        return [
            f"{original_query} controversy",
            f"{original_query} debate",
            f"{original_query} opinions",
            f"{original_query} discussion",
            f"{original_query} reviews",
            f"why {original_query}",
            f"best {original_query}",
            f"worst {original_query}",
            f"{original_query} explained",
            f"{original_query} truth"
        ]
    
    def should_terminate_early(self, progress: float, queries_remaining: int,
                             estimated_max_possible: int, target: int) -> Tuple[bool, str]:
        """Determine if we should terminate early with intelligent reasoning"""
        
        # Calculate if it's mathematically possible to reach target
        max_possible_final = progress + estimated_max_possible
        
        if max_possible_final < target * 0.7:  # Less than 70% of target achievable
            return True, f"Mathematical limit reached. Max possible: {max_possible_final}, Target: {target}"
        
        # Check if we're close enough to target (within 90%)
        if progress >= target * 0.9:
            return True, f"Close enough to target achieved: {progress}/{target} (90%+)"
        
        # Continue if there's still hope
        return False, "Continuing - target still achievable"
    
    def get_smart_dashboard_config(self, user_target: int) -> Dict[str, Any]:
        """Generate smart dashboard configuration based on user target"""
        
        # Calculate recommended settings based on target
        if user_target <= 1000:
            config = {
                'query_variations': 5,
                'processing_mode': 'FAST',
                'estimated_time': '30-60 seconds',
                'recommended_sources': ['youtube'],
                'priority': 'speed'
            }
        elif user_target <= 10000:
            config = {
                'query_variations': 10,
                'processing_mode': 'BALANCED',
                'estimated_time': '1-2 minutes',
                'recommended_sources': ['youtube', 'reddit'],
                'priority': 'balanced'
            }
        elif user_target <= 50000:
            config = {
                'query_variations': 20,
                'processing_mode': 'COMPREHENSIVE',
                'estimated_time': '2-4 minutes',
                'recommended_sources': ['youtube', 'reddit'],
                'priority': 'thoroughness'
            }
        else:
            config = {
                'query_variations': 30,
                'processing_mode': 'MAXIMUM',
                'estimated_time': '4-8 minutes',
                'recommended_sources': ['youtube', 'reddit'],
                'priority': 'maximum_coverage'
            }
        
        return config


# Global smart goal manager instance
smart_goal_manager = SmartGoalManager()