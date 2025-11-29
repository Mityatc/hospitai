"""
HospitAI Agentic AI System
Autonomous decision-making agent that monitors, analyzes, and takes actions.

Agent Architecture:
1. PERCEPTION - Gather and process hospital data
2. REASONING - Analyze patterns and identify issues  
3. PLANNING - Determine optimal actions
4. EXECUTION - Take or recommend actions
5. LEARNING - Track outcomes and improve
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except ImportError:
    GEMINI_AVAILABLE = False


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ActionType(Enum):
    ALERT = "alert"
    RESOURCE_REQUEST = "resource_request"
    STAFF_CALL = "staff_call"
    DIVERSION = "diversion"
    SUPPLY_ORDER = "supply_order"
    PROTOCOL_ACTIVATION = "protocol_activation"


@dataclass
class AgentAction:
    """Represents an action taken or recommended by the agent."""
    action_type: ActionType
    description: str
    priority: int  # 1-5, 5 being highest
    timestamp: datetime = field(default_factory=datetime.now)
    auto_executed: bool = False
    requires_approval: bool = True
    details: Dict = field(default_factory=dict)
    outcome: Optional[str] = None


@dataclass
class AgentThought:
    """Represents a step in the agent's reasoning chain."""
    step: str
    observation: str
    reasoning: str
    conclusion: str
    confidence: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)


# Global agent state
AGENT_LOG = []
AGENT_MEMORY = {
    'past_predictions': [],
    'action_outcomes': [],
    'learned_patterns': []
}


class HospitAIAgent:
    """
    Autonomous AI Agent for hospital surge management.
    
    Implements a ReAct-style agent with:
    - Perception: Data gathering and situation awareness
    - Reasoning: Pattern analysis and risk assessment
    - Planning: Action prioritization and resource allocation
    - Execution: Automated responses and recommendations
    - Learning: Outcome tracking and model improvement
    """
    
    # Thresholds for autonomous action
    THRESHOLDS = {
        'bed_occupancy_warning': 75,
        'bed_occupancy_critical': 90,
        'icu_occupancy_warning': 70,
        'icu_occupancy_critical': 85,
        'ventilator_warning': 60,
        'ventilator_critical': 80,
        'staff_ratio_min': 0.15,
        'flu_surge_threshold': 50,
        'aqi_warning': 100,
        'aqi_critical': 150
    }
    
    def __init__(self, hospital_name="City General Hospital", autonomous_mode=False):
        self.hospital_name = hospital_name
        self.autonomous_mode = autonomous_mode
        self.actions_taken: List[AgentAction] = []
        self.pending_actions: List[AgentAction] = []
        self.reasoning_chain: List[AgentThought] = []
        self.current_situation: Dict = {}
        self.goals = [
            "Maintain patient safety",
            "Optimize resource utilization",
            "Prevent capacity overflow",
            "Ensure adequate staffing",
            "Minimize response time to surges"
        ]
        
    def perceive(self, df) -> Dict[str, Any]:
        """
        PERCEPTION: Gather and process current hospital state.
        """
        latest = df.iloc[-1]
        
        # Calculate key metrics - convert to native Python types
        bed_occupancy = float((latest['occupied_beds'] / latest['total_beds']) * 100)
        icu_occupancy = float((latest['occupied_icu'] / latest['total_icu_beds']) * 100)
        vent_usage = float((latest['ventilators_used'] / latest['total_ventilators']) * 100)
        staff_ratio = float(latest['staff_on_duty'] / max(latest['occupied_beds'], 1))
        
        # Trend analysis
        trends = self._calculate_trends(df)
        
        # Environmental factors - convert to native types
        env_factors = {
            'pollution_aqi': float(latest.get('pollution', 0)),
            'temperature': float(latest.get('temperature', 20)),
            'flu_cases': int(latest.get('flu_cases', 0))
        }
        
        self.current_situation = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'bed_occupancy': float(round(bed_occupancy, 1)),
                'icu_occupancy': float(round(icu_occupancy, 1)),
                'ventilator_usage': float(round(vent_usage, 1)),
                'staff_ratio': float(round(staff_ratio, 3)),
                'total_beds': int(latest['total_beds']),
                'occupied_beds': int(latest['occupied_beds']),
                'available_beds': int(latest['total_beds'] - latest['occupied_beds']),
                'total_icu': int(latest['total_icu_beds']),
                'occupied_icu': int(latest['occupied_icu']),
                'available_icu': int(latest['total_icu_beds'] - latest['occupied_icu'])
            },
            'trends': trends,
            'environment': env_factors,
            'risk_score': int(latest.get('risk_score', 0))
        }
        
        self._add_thought(
            step="PERCEPTION",
            observation=f"Gathered hospital metrics: {bed_occupancy:.1f}% bed occupancy, {icu_occupancy:.1f}% ICU",
            reasoning="Collecting current state data for analysis",
            conclusion="Situation data captured successfully",
            confidence=0.95
        )
        
        return self.current_situation
    
    def _calculate_trends(self, df) -> Dict[str, Any]:
        """Calculate trends from historical data."""
        trends = {
            'bed_change_1d': 0, 'bed_change_3d': 0, 'bed_change_7d': 0,
            'icu_change_3d': 0, 'flu_change_3d': 0,
            'direction': 'stable', 'velocity': 'slow'
        }
        
        if len(df) >= 2:
            trends['bed_change_1d'] = int(df['occupied_beds'].iloc[-1] - df['occupied_beds'].iloc[-2])
        if len(df) >= 3:
            trends['bed_change_3d'] = int(df['occupied_beds'].iloc[-1] - df['occupied_beds'].iloc[-3])
            trends['icu_change_3d'] = int(df['occupied_icu'].iloc[-1] - df['occupied_icu'].iloc[-3])
            trends['flu_change_3d'] = int(df['flu_cases'].iloc[-1] - df['flu_cases'].iloc[-3])
        if len(df) >= 7:
            trends['bed_change_7d'] = int(df['occupied_beds'].iloc[-1] - df['occupied_beds'].iloc[-7])
        
        # Determine direction and velocity
        if trends['bed_change_3d'] > 10:
            trends['direction'] = 'increasing'
            trends['velocity'] = 'rapid' if trends['bed_change_3d'] > 20 else 'moderate'
        elif trends['bed_change_3d'] < -10:
            trends['direction'] = 'decreasing'
            trends['velocity'] = 'rapid' if trends['bed_change_3d'] < -20 else 'moderate'
            
        return trends
    
    def reason(self) -> List[Dict[str, Any]]:
        """
        REASONING: Analyze situation and identify issues/opportunities.
        Returns list of identified issues with severity.
        """
        issues = []
        metrics = self.current_situation.get('metrics', {})
        trends = self.current_situation.get('trends', {})
        env = self.current_situation.get('environment', {})
        
        # Check bed capacity
        bed_occ = metrics.get('bed_occupancy', 0)
        if bed_occ >= self.THRESHOLDS['bed_occupancy_critical']:
            issues.append({
                'type': 'capacity_critical',
                'resource': 'beds',
                'severity': AlertLevel.EMERGENCY,
                'value': bed_occ,
                'message': f"CRITICAL: Bed occupancy at {bed_occ}% - immediate action required"
            })
        elif bed_occ >= self.THRESHOLDS['bed_occupancy_warning']:
            issues.append({
                'type': 'capacity_warning',
                'resource': 'beds',
                'severity': AlertLevel.WARNING,
                'value': bed_occ,
                'message': f"WARNING: Bed occupancy at {bed_occ}% - prepare contingency"
            })
        
        # Check ICU capacity
        icu_occ = metrics.get('icu_occupancy', 0)
        if icu_occ >= self.THRESHOLDS['icu_occupancy_critical']:
            issues.append({
                'type': 'capacity_critical',
                'resource': 'icu',
                'severity': AlertLevel.EMERGENCY,
                'value': icu_occ,
                'message': f"CRITICAL: ICU at {icu_occ}% capacity"
            })
        elif icu_occ >= self.THRESHOLDS['icu_occupancy_warning']:
            issues.append({
                'type': 'capacity_warning',
                'resource': 'icu',
                'severity': AlertLevel.WARNING,
                'value': icu_occ,
                'message': f"WARNING: ICU at {icu_occ}% - monitor closely"
            })
        
        # Check ventilators
        vent_usage = metrics.get('ventilator_usage', 0)
        if vent_usage >= self.THRESHOLDS['ventilator_critical']:
            issues.append({
                'type': 'equipment_critical',
                'resource': 'ventilators',
                'severity': AlertLevel.CRITICAL,
                'value': vent_usage,
                'message': f"CRITICAL: Ventilator usage at {vent_usage}%"
            })
        
        # Check staffing
        staff_ratio = metrics.get('staff_ratio', 1)
        if staff_ratio < self.THRESHOLDS['staff_ratio_min']:
            issues.append({
                'type': 'staffing_shortage',
                'resource': 'staff',
                'severity': AlertLevel.CRITICAL,
                'value': staff_ratio,
                'message': f"CRITICAL: Staff ratio {staff_ratio:.2f} below minimum {self.THRESHOLDS['staff_ratio_min']}"
            })
        
        # Check environmental factors
        aqi = env.get('pollution_aqi', 0)
        if aqi >= self.THRESHOLDS['aqi_critical']:
            issues.append({
                'type': 'environmental_alert',
                'resource': 'air_quality',
                'severity': AlertLevel.WARNING,
                'value': aqi,
                'message': f"High AQI ({aqi}) - expect respiratory admissions increase"
            })
        
        # Check flu surge
        flu = env.get('flu_cases', 0)
        if flu >= self.THRESHOLDS['flu_surge_threshold']:
            issues.append({
                'type': 'disease_surge',
                'resource': 'flu',
                'severity': AlertLevel.WARNING,
                'value': flu,
                'message': f"Flu surge detected: {flu} cases"
            })
        
        # Trend-based predictions
        if trends.get('direction') == 'increasing' and trends.get('velocity') == 'rapid':
            issues.append({
                'type': 'trend_alert',
                'resource': 'capacity',
                'severity': AlertLevel.WARNING,
                'value': trends.get('bed_change_3d', 0),
                'message': f"Rapid increase in admissions: +{trends.get('bed_change_3d', 0)} beds in 3 days"
            })
        
        self._add_thought(
            step="REASONING",
            observation=f"Identified {len(issues)} potential issues",
            reasoning="Compared current metrics against thresholds and analyzed trends",
            conclusion=f"Issues found: {[i['type'] for i in issues]}" if issues else "No critical issues detected",
            confidence=0.85
        )
        
        return issues
    
    def plan(self, issues: List[Dict]) -> List[AgentAction]:
        """
        PLANNING: Generate action plan based on identified issues.
        """
        actions = []
        
        for issue in issues:
            severity = issue['severity']
            issue_type = issue['type']
            
            if issue_type == 'capacity_critical' and issue['resource'] == 'beds':
                actions.append(AgentAction(
                    action_type=ActionType.DIVERSION,
                    description="Activate ambulance diversion protocol",
                    priority=5,
                    requires_approval=not self.autonomous_mode,
                    details={'reason': issue['message'], 'duration_hours': 4}
                ))
                actions.append(AgentAction(
                    action_type=ActionType.PROTOCOL_ACTIVATION,
                    description="Activate surge capacity protocol - open overflow areas",
                    priority=5,
                    requires_approval=True,
                    details={'protocol': 'SURGE_LEVEL_3'}
                ))
                
            elif issue_type == 'capacity_warning' and issue['resource'] == 'beds':
                actions.append(AgentAction(
                    action_type=ActionType.ALERT,
                    description="Alert bed management team - high occupancy",
                    priority=3,
                    requires_approval=False,
                    auto_executed=self.autonomous_mode,
                    details={'recipients': ['bed_management', 'nursing_supervisor']}
                ))
                actions.append(AgentAction(
                    action_type=ActionType.RESOURCE_REQUEST,
                    description="Request discharge planning review for eligible patients",
                    priority=3,
                    requires_approval=False,
                    details={'target': 'case_management'}
                ))
                
            elif issue_type == 'capacity_critical' and issue['resource'] == 'icu':
                actions.append(AgentAction(
                    action_type=ActionType.ALERT,
                    description="URGENT: ICU at critical capacity",
                    priority=5,
                    requires_approval=False,
                    auto_executed=True,
                    details={'recipients': ['icu_director', 'cmo', 'bed_management']}
                ))
                actions.append(AgentAction(
                    action_type=ActionType.RESOURCE_REQUEST,
                    description="Request ICU step-down evaluations",
                    priority=4,
                    requires_approval=False,
                    details={'target': 'icu_team'}
                ))
                
            elif issue_type == 'staffing_shortage':
                actions.append(AgentAction(
                    action_type=ActionType.STAFF_CALL,
                    description="Initiate emergency staff callback",
                    priority=4,
                    requires_approval=not self.autonomous_mode,
                    details={'type': 'callback', 'departments': ['nursing', 'respiratory']}
                ))
                actions.append(AgentAction(
                    action_type=ActionType.ALERT,
                    description="Alert staffing office - critical shortage",
                    priority=4,
                    requires_approval=False,
                    auto_executed=True,
                    details={'recipients': ['staffing_office', 'nursing_director']}
                ))
                
            elif issue_type == 'equipment_critical':
                actions.append(AgentAction(
                    action_type=ActionType.SUPPLY_ORDER,
                    description="Request emergency ventilator allocation from regional pool",
                    priority=5,
                    requires_approval=True,
                    details={'equipment': 'ventilators', 'quantity': 5}
                ))
                
            elif issue_type == 'environmental_alert':
                actions.append(AgentAction(
                    action_type=ActionType.ALERT,
                    description=f"Environmental alert: {issue['message']}",
                    priority=2,
                    requires_approval=False,
                    auto_executed=True,
                    details={'type': 'environmental', 'aqi': issue['value']}
                ))
                
            elif issue_type == 'disease_surge':
                actions.append(AgentAction(
                    action_type=ActionType.PROTOCOL_ACTIVATION,
                    description="Consider activating flu surge protocol",
                    priority=3,
                    requires_approval=True,
                    details={'protocol': 'FLU_SURGE', 'cases': issue['value']}
                ))
                
            elif issue_type == 'trend_alert':
                actions.append(AgentAction(
                    action_type=ActionType.ALERT,
                    description="Trend alert: Rapid admission increase detected",
                    priority=3,
                    requires_approval=False,
                    auto_executed=True,
                    details={'trend': issue['value']}
                ))
        
        # Sort by priority
        actions.sort(key=lambda x: x.priority, reverse=True)
        
        self._add_thought(
            step="PLANNING",
            observation=f"Generated {len(actions)} potential actions",
            reasoning="Mapped issues to appropriate response protocols",
            conclusion=f"Top priority: {actions[0].description if actions else 'No actions needed'}",
            confidence=0.80
        )
        
        return actions
    
    def execute(self, actions: List[AgentAction]) -> Dict[str, Any]:
        """
        EXECUTION: Execute or queue actions based on approval requirements.
        """
        executed = []
        pending = []
        
        for action in actions:
            if action.auto_executed or (self.autonomous_mode and not action.requires_approval):
                # Auto-execute
                action.auto_executed = True
                action.outcome = "Executed automatically"
                executed.append(action)
                self.actions_taken.append(action)
                AGENT_LOG.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': action.description,
                    'type': action.action_type.value,
                    'auto': True
                })
            else:
                # Queue for approval
                pending.append(action)
                self.pending_actions.append(action)
        
        self._add_thought(
            step="EXECUTION",
            observation=f"Executed {len(executed)} actions, {len(pending)} pending approval",
            reasoning="Actions executed based on autonomy settings and approval requirements",
            conclusion="Execution phase complete",
            confidence=0.90
        )
        
        return {
            'executed': executed,
            'pending': pending,
            'total_actions': len(actions)
        }
    
    def run_cycle(self, df) -> Dict[str, Any]:
        """
        Run a complete agent cycle: Perceive -> Reason -> Plan -> Execute
        """
        self.reasoning_chain = []  # Reset for new cycle
        
        # 1. PERCEIVE
        situation = self.perceive(df)
        
        # 2. REASON
        issues = self.reason()
        
        # 3. PLAN
        actions = self.plan(issues)
        
        # 4. EXECUTE
        results = self.execute(actions)
        
        # Store in memory for learning
        AGENT_MEMORY['past_predictions'].append({
            'timestamp': datetime.now().isoformat(),
            'situation': situation,
            'issues': len(issues),
            'actions': len(actions)
        })
        
        return {
            'situation': situation,
            'issues': issues,
            'actions': results,
            'reasoning_chain': [self._thought_to_dict(t) for t in self.reasoning_chain]
        }
    
    def get_ai_analysis(self, df) -> str:
        """
        Get detailed AI analysis using Gemini if available.
        """
        situation = self.current_situation or self.perceive(df)
        issues = self.reason()
        
        if not GEMINI_AVAILABLE:
            return self._generate_fallback_analysis(situation, issues)
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""You are an AI hospital operations advisor. Analyze this situation and provide actionable recommendations.

CURRENT HOSPITAL STATUS ({self.hospital_name}):
- Bed Occupancy: {situation['metrics']['bed_occupancy']}%
- ICU Occupancy: {situation['metrics']['icu_occupancy']}%
- Ventilator Usage: {situation['metrics']['ventilator_usage']}%
- Staff-to-Patient Ratio: {situation['metrics']['staff_ratio']}
- Available Beds: {situation['metrics']['available_beds']}
- Available ICU: {situation['metrics']['available_icu']}

TRENDS:
- 3-day bed change: {situation['trends']['bed_change_3d']} patients
- Trend direction: {situation['trends']['direction']} ({situation['trends']['velocity']})

ENVIRONMENTAL FACTORS:
- Air Quality Index: {situation['environment']['pollution_aqi']}
- Flu Cases: {situation['environment']['flu_cases']}

IDENTIFIED ISSUES: {len(issues)}
{chr(10).join([f"- {i['message']}" for i in issues]) if issues else "- No critical issues"}

Provide:
1. Overall situation assessment (1-2 sentences)
2. Top 3 recommended actions with priority
3. 24-hour outlook prediction
4. Any early warning signs to monitor

Keep response concise and actionable."""

            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return self._generate_fallback_analysis(situation, issues)
    
    def _generate_fallback_analysis(self, situation: Dict, issues: List) -> str:
        """Generate analysis without AI API."""
        metrics = situation.get('metrics', {})
        trends = situation.get('trends', {})
        
        # Determine overall status
        bed_occ = metrics.get('bed_occupancy', 0)
        if bed_occ >= 90:
            status = "🔴 CRITICAL"
            outlook = "High risk of capacity overflow within 24 hours"
        elif bed_occ >= 75:
            status = "🟡 ELEVATED"
            outlook = "Monitor closely, prepare contingency plans"
        else:
            status = "🟢 STABLE"
            outlook = "Normal operations expected"
        
        analysis = f"""## Hospital Status: {status}

**Current Metrics:**
- Bed Occupancy: {bed_occ}% ({metrics.get('available_beds', 0)} available)
- ICU Occupancy: {metrics.get('icu_occupancy', 0)}% ({metrics.get('available_icu', 0)} available)
- Staff Ratio: {metrics.get('staff_ratio', 0):.2f}

**Trend Analysis:**
- Direction: {trends.get('direction', 'stable').title()}
- 3-day change: {trends.get('bed_change_3d', 0):+d} beds

**Issues Detected:** {len(issues)}
"""
        if issues:
            for issue in issues[:3]:
                analysis += f"- {issue['message']}\n"
        else:
            analysis += "- No critical issues at this time\n"
        
        analysis += f"\n**24-Hour Outlook:** {outlook}"
        
        return analysis
    
    def _add_thought(self, step: str, observation: str, reasoning: str, conclusion: str, confidence: float):
        """Add a thought to the reasoning chain."""
        self.reasoning_chain.append(AgentThought(
            step=step,
            observation=observation,
            reasoning=reasoning,
            conclusion=conclusion,
            confidence=confidence
        ))
    
    def _thought_to_dict(self, thought: AgentThought) -> Dict:
        """Convert thought to dictionary for serialization."""
        return {
            'step': thought.step,
            'observation': thought.observation,
            'reasoning': thought.reasoning,
            'conclusion': thought.conclusion,
            'confidence': thought.confidence,
            'timestamp': thought.timestamp.isoformat()
        }
    
    def get_reasoning_trace(self) -> str:
        """Get human-readable reasoning trace."""
        trace = "## Agent Reasoning Trace\n\n"
        for i, thought in enumerate(self.reasoning_chain, 1):
            trace += f"**Step {i}: {thought.step}**\n"
            trace += f"- Observation: {thought.observation}\n"
            trace += f"- Reasoning: {thought.reasoning}\n"
            trace += f"- Conclusion: {thought.conclusion}\n"
            trace += f"- Confidence: {thought.confidence:.0%}\n\n"
        return trace
    
    def get_pending_actions_summary(self) -> List[Dict]:
        """Get summary of pending actions requiring approval."""
        return [{
            'action': a.description,
            'type': a.action_type.value,
            'priority': a.priority,
            'details': a.details
        } for a in self.pending_actions]
    
    def approve_action(self, index: int) -> bool:
        """Approve and execute a pending action."""
        if 0 <= index < len(self.pending_actions):
            action = self.pending_actions.pop(index)
            action.outcome = "Approved and executed"
            self.actions_taken.append(action)
            AGENT_LOG.append({
                'timestamp': datetime.now().isoformat(),
                'action': action.description,
                'type': action.action_type.value,
                'auto': False,
                'approved': True
            })
            return True
        return False
    
    def reject_action(self, index: int) -> bool:
        """Reject a pending action."""
        if 0 <= index < len(self.pending_actions):
            action = self.pending_actions.pop(index)
            action.outcome = "Rejected by operator"
            AGENT_LOG.append({
                'timestamp': datetime.now().isoformat(),
                'action': action.description,
                'type': action.action_type.value,
                'auto': False,
                'approved': False
            })
            return True
        return False


def get_agent_log() -> List[Dict]:
    """Get the global agent action log."""
    return AGENT_LOG


def get_agent_memory() -> Dict:
    """Get the agent's memory state."""
    return AGENT_MEMORY
