#!/usr/bin/env python3
"""
Session Analysis Example - Analyze and extract insights from saved sessions.

This example demonstrates:
- Loading and parsing session files
- Extracting usage patterns and statistics
- Cost analysis and optimization suggestions
- Conversation quality metrics
- Export to different formats

Usage:
    python3 example_session_analysis.py
"""

import os
import json
import glob
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
import statistics

@dataclass
class SessionSummary:
    """Summary statistics for a single session."""
    filename: str
    model: str
    created_at: datetime
    system_prompt: Optional[str]
    turns: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_cost: float
    avg_latency: float
    success_rate: float
    conversation_length_chars: int

@dataclass
class ConversationAnalysis:
    """Analysis of conversation patterns."""
    avg_question_length: float
    avg_response_length: float
    most_common_topics: List[Tuple[str, int]]
    question_types: Dict[str, int]
    complexity_score: float

class SessionAnalyzer:
    """Analyze LLM conversation sessions."""
    
    def __init__(self, sessions_dir: str = "./runs"):
        """
        Initialize session analyzer.
        
        Args:
            sessions_dir: Directory containing session JSON files
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions: List[Dict[str, Any]] = []
        self.summaries: List[SessionSummary] = []
        
    def load_sessions(self, pattern: str = "*.json") -> int:
        """
        Load all session files matching the pattern.
        
        Args:
            pattern: Glob pattern for session files
            
        Returns:
            Number of successfully loaded sessions
        """
        
        session_files = list(self.sessions_dir.glob(pattern))
        
        print(f"📂 Found {len(session_files)} session files in {self.sessions_dir}")
        
        loaded_count = 0
        failed_files = []
        
        for session_file in session_files:
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    session_data['_filename'] = session_file.name
                    self.sessions.append(session_data)
                    loaded_count += 1
                    
            except json.JSONDecodeError as e:
                failed_files.append((session_file.name, f"JSON decode error: {e}"))
            except Exception as e:
                failed_files.append((session_file.name, f"Error: {e}"))
        
        if failed_files:
            print(f"⚠️  Failed to load {len(failed_files)} files:")
            for filename, error in failed_files[:5]:  # Show first 5
                print(f"   {filename}: {error}")
            if len(failed_files) > 5:
                print(f"   ... and {len(failed_files) - 5} more")
        
        print(f"✅ Successfully loaded {loaded_count} sessions")
        return loaded_count
    
    def analyze_sessions(self) -> List[SessionSummary]:
        """
        Analyze all loaded sessions and create summaries.
        
        Returns:
            List of session summaries
        """
        
        summaries = []
        
        print("🔍 Analyzing sessions...")
        
        for session in self.sessions:
            try:
                summary = self._analyze_single_session(session)
                summaries.append(summary)
            except Exception as e:
                print(f"⚠️  Error analyzing {session.get('_filename', 'unknown')}: {e}")
        
        self.summaries = summaries
        print(f"📊 Analyzed {len(summaries)} sessions")
        
        return summaries
    
    def _analyze_single_session(self, session: Dict[str, Any]) -> SessionSummary:
        """Analyze a single session and create summary."""
        
        filename = session.get('_filename', 'unknown')
        model = session.get('model', 'unknown')
        
        # Parse creation time
        created_at_str = session.get('created_at', '')
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        except:
            created_at = datetime.now()
        
        system_prompt = session.get('system')
        turns = len(session.get('turns', []))
        
        # Calculate token usage
        usage_totals = session.get('usage_totals', {})
        total_tokens = usage_totals.get('total_tokens', 0)
        prompt_tokens = usage_totals.get('prompt_tokens', 0)
        completion_tokens = usage_totals.get('completion_tokens', 0)
        
        # Calculate costs and latency
        total_cost = 0.0
        latencies = []
        successful_turns = 0
        
        for turn in session.get('turns', []):
            cost = turn.get('cost_estimate', 0.0)
            if isinstance(cost, (int, float)):
                total_cost += cost
            
            latency = turn.get('latency_ms')
            if latency is not None:
                latencies.append(latency)
                successful_turns += 1
        
        avg_latency = statistics.mean(latencies) if latencies else 0.0
        success_rate = successful_turns / turns if turns > 0 else 0.0
        
        # Calculate conversation length
        conversation_length = 0
        for turn in session.get('turns', []):
            for message in turn.get('messages', []):
                content = message.get('content', '')
                conversation_length += len(content)
        
        return SessionSummary(
            filename=filename,
            model=model,
            created_at=created_at,
            system_prompt=system_prompt,
            turns=turns,
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_cost=total_cost,
            avg_latency=avg_latency,
            success_rate=success_rate,
            conversation_length_chars=conversation_length
        )
    
    def analyze_conversation_patterns(self) -> Dict[str, ConversationAnalysis]:
        """Analyze conversation patterns by model."""
        
        print("🔍 Analyzing conversation patterns...")
        
        model_conversations = defaultdict(list)
        
        # Group conversations by model
        for session in self.sessions:
            model = session.get('model', 'unknown')
            turns = session.get('turns', [])
            
            for turn in turns:
                messages = turn.get('messages', [])
                user_msg = None
                assistant_msg = None
                
                for msg in messages:
                    if msg.get('role') == 'user':
                        user_msg = msg.get('content', '')
                    elif msg.get('role') == 'assistant':
                        assistant_msg = msg.get('content', '')
                
                if user_msg and assistant_msg:
                    model_conversations[model].append((user_msg, assistant_msg))
        
        # Analyze patterns for each model
        analyses = {}
        
        for model, conversations in model_conversations.items():
            if not conversations:
                continue
                
            # Calculate average lengths
            question_lengths = [len(q) for q, _ in conversations]
            response_lengths = [len(r) for _, r in conversations]
            
            avg_question_length = statistics.mean(question_lengths)
            avg_response_length = statistics.mean(response_lengths)
            
            # Analyze question types
            question_types = self._analyze_question_types([q for q, _ in conversations])
            
            # Extract topics (simple keyword analysis)
            all_text = ' '.join([f"{q} {r}" for q, r in conversations])
            topics = self._extract_topics(all_text)
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(conversations)
            
            analyses[model] = ConversationAnalysis(
                avg_question_length=avg_question_length,
                avg_response_length=avg_response_length,
                most_common_topics=topics[:10],  # Top 10
                question_types=question_types,
                complexity_score=complexity_score
            )
        
        return analyses
    
    def _analyze_question_types(self, questions: List[str]) -> Dict[str, int]:
        """Analyze types of questions asked."""
        
        types = defaultdict(int)
        
        for question in questions:
            q_lower = question.lower().strip()
            
            if q_lower.startswith(('what', 'what is', 'what are')):
                types['definition'] += 1
            elif q_lower.startswith(('how', 'how do', 'how to')):
                types['how_to'] += 1
            elif q_lower.startswith(('why', 'why is', 'why do')):
                types['explanation'] += 1
            elif q_lower.startswith(('can you', 'could you', 'please')):
                types['request'] += 1
            elif q_lower.startswith(('write', 'create', 'make', 'generate')):
                types['creation'] += 1
            elif '?' in question:
                types['question'] += 1
            else:
                types['statement'] += 1
        
        return dict(types)
    
    def _extract_topics(self, text: str) -> List[Tuple[str, int]]:
        """Extract common topics from conversation text."""
        
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Filter out common words
        stop_words = {
            'this', 'that', 'with', 'have', 'will', 'from', 'they', 'them',
            'been', 'their', 'said', 'each', 'which', 'does', 'when',
            'what', 'how', 'why', 'where', 'who', 'would', 'could', 'should',
            'like', 'just', 'also', 'some', 'more', 'very', 'much', 'many',
            'most', 'such', 'even', 'well', 'good', 'best', 'better',
            'example', 'examples', 'using', 'used', 'uses', 'help', 'helps'
        }
        
        filtered_words = [w for w in words if w not in stop_words and len(w) > 4]
        
        # Count occurrences
        word_counts = Counter(filtered_words)
        
        return word_counts.most_common(20)
    
    def _calculate_complexity_score(self, conversations: List[Tuple[str, str]]) -> float:
        """Calculate a complexity score for conversations."""
        
        if not conversations:
            return 0.0
        
        total_score = 0.0
        
        for question, response in conversations:
            # Factors that increase complexity
            score = 0.0
            
            # Length factor
            score += min(len(question) / 100, 5.0)  # Cap at 5 points
            score += min(len(response) / 500, 10.0)  # Cap at 10 points
            
            # Technical terms factor
            tech_terms = ['function', 'algorithm', 'implementation', 'architecture',
                         'optimization', 'performance', 'debugging', 'analysis']
            
            tech_count = sum(1 for term in tech_terms 
                           if term in question.lower() or term in response.lower())
            score += tech_count * 2
            
            # Code presence factor
            if '```' in response or 'def ' in response or 'class ' in response:
                score += 5.0
            
            total_score += score
        
        return total_score / len(conversations)
    
    def print_overview_stats(self):
        """Print overview statistics."""
        
        if not self.summaries:
            print("❌ No session summaries available. Run analyze_sessions() first.")
            return
        
        print("\\n📊 Session Overview")
        print("=" * 50)
        
        # Basic stats
        total_sessions = len(self.summaries)
        total_turns = sum(s.turns for s in self.summaries)
        total_tokens = sum(s.total_tokens for s in self.summaries)
        total_cost = sum(s.total_cost for s in self.summaries)
        
        print(f"Total sessions: {total_sessions}")
        print(f"Total turns: {total_turns:,}")
        print(f"Total tokens: {total_tokens:,}")
        print(f"Total cost: ${total_cost:.6f}")
        
        if total_sessions > 0:
            print(f"Average turns per session: {total_turns / total_sessions:.1f}")
            print(f"Average cost per session: ${total_cost / total_sessions:.6f}")
        
        # Date range
        dates = [s.created_at for s in self.summaries]
        if dates:
            earliest = min(dates)
            latest = max(dates)
            print(f"Date range: {earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}")
        
        # Model usage
        model_counts = Counter(s.model for s in self.summaries)
        print(f"\\n🤖 Models used:")
        for model, count in model_counts.most_common(5):
            print(f"   {model}: {count} sessions")
    
    def print_cost_analysis(self):
        """Print detailed cost analysis."""
        
        print("\\n💰 Cost Analysis")
        print("=" * 50)
        
        if not self.summaries:
            return
        
        # Overall cost stats
        costs = [s.total_cost for s in self.summaries]
        tokens = [s.total_tokens for s in self.summaries]
        
        if costs:
            print(f"Total spending: ${sum(costs):.6f}")
            print(f"Average cost per session: ${statistics.mean(costs):.6f}")
            print(f"Median cost per session: ${statistics.median(costs):.6f}")
            
            if len(costs) > 1:
                print(f"Cost std deviation: ${statistics.stdev(costs):.6f}")
        
        # Cost by model
        model_costs = defaultdict(list)
        model_tokens = defaultdict(list)
        
        for summary in self.summaries:
            model_costs[summary.model].append(summary.total_cost)
            model_tokens[summary.model].append(summary.total_tokens)
        
        print("\\n💸 Cost by model:")
        for model in model_costs:
            costs = model_costs[model]
            tokens = model_tokens[model]
            
            total_cost = sum(costs)
            total_tokens = sum(tokens)
            avg_cost = statistics.mean(costs) if costs else 0
            cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0
            
            print(f"   {model}:")
            print(f"      Sessions: {len(costs)}")
            print(f"      Total cost: ${total_cost:.6f}")
            print(f"      Avg per session: ${avg_cost:.6f}")
            print(f"      Cost per token: ${cost_per_token:.8f}")
        
        # Daily spending trend (if multiple days)
        daily_costs = defaultdict(float)
        for summary in self.summaries:
            date_key = summary.created_at.strftime('%Y-%m-%d')
            daily_costs[date_key] += summary.total_cost
        
        if len(daily_costs) > 1:
            print("\\n📅 Daily spending trend (last 7 days):")
            sorted_days = sorted(daily_costs.items(), key=lambda x: x[0])[-7:]
            for date, cost in sorted_days:
                print(f"   {date}: ${cost:.6f}")
    
    def print_performance_analysis(self):
        """Print performance analysis."""
        
        print("\\n⚡ Performance Analysis")
        print("=" * 50)
        
        if not self.summaries:
            return
        
        # Response time analysis
        latencies = [s.avg_latency for s in self.summaries if s.avg_latency > 0]
        
        if latencies:
            print(f"Average response time: {statistics.mean(latencies):.1f}ms")
            print(f"Median response time: {statistics.median(latencies):.1f}ms")
            print(f"Fastest response: {min(latencies):.1f}ms")
            print(f"Slowest response: {max(latencies):.1f}ms")
        
        # Success rate analysis
        success_rates = [s.success_rate for s in self.summaries]
        if success_rates:
            avg_success = statistics.mean(success_rates) * 100
            print(f"\\nOverall success rate: {avg_success:.1f}%")
        
        # Performance by model
        model_performance = defaultdict(list)
        for summary in self.summaries:
            if summary.avg_latency > 0:
                model_performance[summary.model].append(summary.avg_latency)
        
        if model_performance:
            print("\\n⚡ Response time by model:")
            for model, latencies in model_performance.items():
                avg_latency = statistics.mean(latencies)
                print(f"   {model}: {avg_latency:.1f}ms avg")
        
        # Token efficiency
        model_efficiency = defaultdict(list)
        for summary in self.summaries:
            if summary.total_tokens > 0 and summary.avg_latency > 0:
                tokens_per_second = (summary.total_tokens / summary.turns) / (summary.avg_latency / 1000)
                model_efficiency[summary.model].append(tokens_per_second)
        
        if model_efficiency:
            print("\\n🏃 Token generation speed by model:")
            for model, speeds in model_efficiency.items():
                avg_speed = statistics.mean(speeds)
                print(f"   {model}: {avg_speed:.1f} tokens/second")
    
    def find_optimization_opportunities(self) -> List[str]:
        """Identify optimization opportunities."""
        
        opportunities = []
        
        if not self.summaries:
            return ["No session data available for analysis"]
        
        # High cost sessions
        high_cost_sessions = [s for s in self.summaries if s.total_cost > 0.05]
        if high_cost_sessions:
            opportunities.append(
                f"Found {len(high_cost_sessions)} high-cost sessions (>${0.05:.3f}). "
                f"Consider using cheaper models for simple tasks."
            )
        
        # Model usage patterns
        model_costs = defaultdict(list)
        for summary in self.summaries:
            model_costs[summary.model].append(summary.total_cost)
        
        # Find expensive models used frequently
        for model, costs in model_costs.items():
            if len(costs) > 5 and statistics.mean(costs) > 0.02:
                opportunities.append(
                    f"Model '{model}' used {len(costs)} times with avg cost "
                    f"${statistics.mean(costs):.4f}. Consider alternatives for routine tasks."
                )
        
        # Long conversations that might benefit from context management
        long_sessions = [s for s in self.summaries if s.turns > 10]
        if long_sessions:
            opportunities.append(
                f"Found {len(long_sessions)} long conversations (>10 turns). "
                f"Consider breaking into smaller sessions or using context reset."
            )
        
        # Poor success rates
        failed_sessions = [s for s in self.summaries if s.success_rate < 0.9]
        if failed_sessions:
            opportunities.append(
                f"Found {len(failed_sessions)} sessions with high failure rates. "
                f"Check for model availability or API issues."
            )
        
        return opportunities if opportunities else ["No specific optimization opportunities identified."]
    
    def export_summary_report(self, filename: str):
        """Export comprehensive summary report."""
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'sessions_analyzed': len(self.summaries),
            'overview': {
                'total_sessions': len(self.summaries),
                'total_turns': sum(s.turns for s in self.summaries),
                'total_tokens': sum(s.total_tokens for s in self.summaries),
                'total_cost': sum(s.total_cost for s in self.summaries),
            },
            'model_usage': dict(Counter(s.model for s in self.summaries)),
            'cost_breakdown': {},
            'optimization_opportunities': self.find_optimization_opportunities(),
            'session_details': [
                {
                    'filename': s.filename,
                    'model': s.model,
                    'created_at': s.created_at.isoformat(),
                    'turns': s.turns,
                    'tokens': s.total_tokens,
                    'cost': s.total_cost,
                    'avg_latency': s.avg_latency
                }
                for s in self.summaries
            ]
        }
        
        # Add cost breakdown by model
        model_costs = defaultdict(float)
        for summary in self.summaries:
            model_costs[summary.model] += summary.total_cost
        
        report['cost_breakdown'] = dict(model_costs)
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"💾 Summary report exported to: {filename}")

def main():
    """Main demonstration function."""
    
    print("📊 Session Analysis Examples")
    print("Analyze your LLM conversation sessions for insights and optimization.")
    print()
    
    # Check if sessions directory exists
    sessions_dir = "./runs"
    if not Path(sessions_dir).exists():
        print(f"❌ Sessions directory '{sessions_dir}' not found.")
        print("Make sure you have some chat sessions saved first.")
        print("Try running: llm chat --model openai/gpt-4o-mini")
        sys.exit(1)
    
    # Initialize analyzer
    analyzer = SessionAnalyzer(sessions_dir)
    
    # Load sessions
    loaded_count = analyzer.load_sessions()
    if loaded_count == 0:
        print("❌ No valid session files found.")
        print("Create some sessions first by running chat commands.")
        sys.exit(1)
    
    # Analyze sessions
    analyzer.analyze_sessions()
    
    # Interactive choice
    print("\\n🎯 Choose analysis type:")
    print("1. Overview statistics")
    print("2. Cost analysis")
    print("3. Performance analysis")  
    print("4. Optimization opportunities")
    print("5. Conversation patterns")
    print("6. Full report (all analyses)")
    print("7. Export summary report")
    print("0. Exit")
    
    choice = input("\\nEnter your choice (0-7): ").strip()
    
    if choice == "1":
        analyzer.print_overview_stats()
    elif choice == "2":
        analyzer.print_cost_analysis()
    elif choice == "3":
        analyzer.print_performance_analysis()
    elif choice == "4":
        opportunities = analyzer.find_optimization_opportunities()
        print("\\n🎯 Optimization Opportunities")
        print("=" * 50)
        for i, opportunity in enumerate(opportunities, 1):
            print(f"{i}. {opportunity}")
    elif choice == "5":
        patterns = analyzer.analyze_conversation_patterns()
        print("\\n💬 Conversation Patterns")
        print("=" * 50)
        for model, analysis in patterns.items():
            print(f"\\n🤖 {model}:")
            print(f"   Avg question length: {analysis.avg_question_length:.0f} chars")
            print(f"   Avg response length: {analysis.avg_response_length:.0f} chars")
            print(f"   Complexity score: {analysis.complexity_score:.1f}")
            print(f"   Question types: {dict(analysis.question_types)}")
            if analysis.most_common_topics:
                topics = [topic for topic, count in analysis.most_common_topics[:5]]
                print(f"   Common topics: {', '.join(topics)}")
    elif choice == "6":
        analyzer.print_overview_stats()
        analyzer.print_cost_analysis()
        analyzer.print_performance_analysis()
        
        opportunities = analyzer.find_optimization_opportunities()
        print("\\n🎯 Optimization Opportunities")
        print("=" * 50)
        for i, opportunity in enumerate(opportunities, 1):
            print(f"{i}. {opportunity}")
    elif choice == "7":
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"session_analysis_report_{timestamp}.json"
        analyzer.export_summary_report(filename)
    elif choice == "0":
        print("👋 Goodbye!")
        sys.exit(0)
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    print("\\n🎉 Analysis completed!")
    print("\\n📖 Next steps:")
    print("• Review optimization opportunities to reduce costs")
    print("• Consider model alternatives based on usage patterns")
    print("• Monitor performance trends over time")
    print("• Export reports for deeper analysis")

if __name__ == "__main__":
    main()