"""
HospitAI Agentic AI System
Autonomous decision-making agent for hospital surge management.
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

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
    action_type: ActionType
    description: str
    priority: int
    timestamp: datetime = field(default_factory=datetime.now)
    auto_executed: bool = False
    requires_approval: bool = True
    details: Dict = field(default_factory=dict)
    outcome: Optional[str] = None


@dataclass
class AgentThought:
    step: str
    observation: str
    reasoning: str
    conclusion: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


AGENT_LOG = []
AGENT_MEMORY = {'past_predictions': [], 'action_outcomes': [], 'learned_patterns': []}


class HospitAIAgent:
    THRESHOLDS = {
        'bed_occupancy_warning': 75, 'bed_occupancy_critical': 90,
        'icu_occupancy_warning': 70, 'icu_occupancy_critical': 85,
        'ventilator_warning': 60, 'ventilator_critical': 80,
        'staff_ratio_min': 0.15, 'flu_surge_threshold': 50,
        'aqi_warning': 100, 'aqi_critical': 150
    }

    def __init__(self, hospital_name="City General Hospital", autonomous_mode=False):
        self.hospital_name = hospital_name
        self.autonomous_mode = autonomous_mode
        self.actions_taken: List[AgentAction] = []
        self.pending_actions: List[AgentAction] = []
        self.reasoning_chain: List[AgentThought] = []
        self.current_situation: Dict = {}

    def perceive(self, df) -> Dict[str, Any]:
        latest = df.iloc[-1]
        bed_occupancy = float((latest['occupied_beds'] / latest['total_beds']) * 100)
        icu_occupancy = float((latest['occupied_icu'] / latest['total_icu_beds']) * 100)
        vent_usage = float((latest['ventilators_used'] / latest['total_ventilators']) * 100)
        staff_ratio = float(latest['staff_on_duty'] / max(latest['occupied_beds'], 1))
        trends = self._calculate_trends(df)
        env_factors = {
            'pollution_aqi': float(latest.get('pollution', 0)),
            'temperature': float(latest.get('temperature', 20)),
            'flu_cases': int(latest.get('flu_cases', 0))
        }
        self.current_situation = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'bed_occupancy': round(bed_occupancy, 1), 'icu_occupancy': round(icu_occupancy, 1),
                'ventilator_usage': round(vent_usage, 1), 'staff_ratio': round(staff_ratio, 3),
                'total_beds': int(latest['total_beds']), 'occupied_beds': int(latest['occupied_beds']),
                'available_beds': int(latest['total_beds'] - latest['occupied_beds']),
                'total_icu': int(latest['total_icu_beds']), 'occupied_icu': int(latest['occupied_icu']),
                'available_icu': int(latest['total_icu_beds'] - latest['occupied_icu'])
            },
            'trends': trends, 'environment': env_factors,
            'risk_score': int(latest.get('risk_score', 0))
        }
        self._add_thought("PERCEPTION", f"Gathered metrics: {bed_occupancy:.1f}% beds, {icu_occupancy:.1f}% ICU",
                         "Collecting state data", "Data captured", 0.95)
        return self.current_situation

    def _calculate_trends(self, df) -> Dict[str, Any]:
        trends = {'bed_change_1d': 0, 'bed_change_3d': 0, 'bed_change_7d': 0,
                  'icu_change_3d': 0, 'flu_change_3d': 0, 'direction': 'stable', 'velocity': 'slow'}
        if len(df) >= 2:
            trends['bed_change_1d'] = int(df['occupied_beds'].iloc[-1] - df['occupied_beds'].iloc[-2])
        if len(df) >= 3:
            trends['bed_change_3d'] = int(df['occupied_beds'].iloc[-1] - df['occupied_beds'].iloc[-3])
            trends['icu_change_3d'] = int(df['occupied_icu'].iloc[-1] - df['occupied_icu'].iloc[-3])
            trends['flu_change_3d'] = int(df['flu_cases'].iloc[-1] - df['flu_cases'].iloc[-3])
        if len(df) >= 7:
            trends['bed_change_7d'] = int(df['occupied_beds'].iloc[-1] - df['occupied_beds'].iloc[-7])
        if trends['bed_change_3d'] > 10:
            trends['direction'] = 'increasing'
            trends['velocity'] = 'rapid' if trends['bed_change_3d'] > 20 else 'moderate'
        elif trends['bed_change_3d'] < -10:
            trends['direction'] = 'decreasing'
            trends['velocity'] = 'rapid' if trends['bed_change_3d'] < -20 else 'moderate'
        return trends

    def reason(self) -> List[Dict[str, Any]]:
        issues = []
        metrics = self.current_situation.get('metrics', {})
        env = self.current_situation.get('environment', {})
        trends = self.current_situation.get('trends', {})
        
        bed_occ = metrics.get('bed_occupancy', 0)
        if bed_occ >= self.THRESHOLDS['bed_occupancy_critical']:
            issues.append({'type': 'capacity_critical', 'resource': 'beds', 'severity': AlertLevel.EMERGENCY,
                          'value': bed_occ, 'message': f"CRITICAL: Bed occupancy at {bed_occ}%"})
        elif bed_occ >= self.THRESHOLDS['bed_occupancy_warning']:
            issues.append({'type': 'capacity_warning', 'resource': 'beds', 'severity': AlertLevel.WARNING,
                          'value': bed_occ, 'message': f"WARNING: Bed occupancy at {bed_occ}%"})
        
        icu_occ = metrics.get('icu_occupancy', 0)
        if icu_occ >= self.THRESHOLDS['icu_occupancy_critical']:
            issues.append({'type': 'capacity_critical', 'resource': 'icu', 'severity': AlertLevel.EMERGENCY,
                          'value': icu_occ, 'message': f"CRITICAL: ICU at {icu_occ}%"})
        elif icu_occ >= self.THRESHOLDS['icu_occupancy_warning']:
            issues.append({'type': 'capacity_warning', 'resource': 'icu', 'severity': AlertLevel.WARNING,
                          'value': icu_occ, 'message': f"WARNING: ICU at {icu_occ}%"})
        
        vent_usage = metrics.get('ventilator_usage', 0)
        if vent_usage >= self.THRESHOLDS['ventilator_critical']:
            issues.append({'type': 'equipment_critical', 'resource': 'ventilators', 'severity': AlertLevel.CRITICAL,
                          'value': vent_usage, 'message': f"CRITICAL: Ventilator usage at {vent_usage}%"})
        
        staff_ratio = metrics.get('staff_ratio', 1)
        if staff_ratio < self.THRESHOLDS['staff_ratio_min']:
            issues.append({'type': 'staffing_shortage', 'resource': 'staff', 'severity': AlertLevel.CRITICAL,
                          'value': staff_ratio, 'message': f"CRITICAL: Staff ratio {staff_ratio:.2f}"})
        
        aqi = env.get('pollution_aqi', 0)
        if aqi >= self.THRESHOLDS['aqi_critical']:
            issues.append({'type': 'environmental_alert', 'resource': 'air_quality', 'severity': AlertLevel.WARNING,
                          'value': aqi, 'message': f"High AQI ({aqi})"})
        
        flu = env.get('flu_cases', 0)
        if flu >= self.THRESHOLDS['flu_surge_threshold']:
            issues.append({'type': 'disease_surge', 'resource': 'flu', 'severity': AlertLevel.WARNING,
                          'value': flu, 'message': f"Flu surge: {flu} cases"})
        
        if trends.get('direction') == 'increasing' and trends.get('velocity') == 'rapid':
            issues.append({'type': 'trend_alert', 'resource': 'capacity', 'severity': AlertLevel.WARNING,
                          'value': trends.get('bed_change_3d', 0), 'message': f"Rapid increase: +{trends.get('bed_change_3d', 0)} beds"})
        
        self._add_thought("REASONING", f"Identified {len(issues)} issues", "Threshold analysis", 
                         f"Issues: {[i['type'] for i in issues]}" if issues else "No issues", 0.85)
        return issues


    def plan(self, issues: List[Dict]) -> List[AgentAction]:
        actions = []
        for issue in issues:
            issue_type = issue['type']
            if issue_type == 'capacity_critical' and issue['resource'] == 'beds':
                actions.append(AgentAction(ActionType.DIVERSION, "Activate ambulance diversion", 5,
                              requires_approval=not self.autonomous_mode, details={'reason': issue['message']}))
                actions.append(AgentAction(ActionType.PROTOCOL_ACTIVATION, "Activate surge protocol", 5,
                              requires_approval=True, details={'protocol': 'SURGE_LEVEL_3'}))
            elif issue_type == 'capacity_warning' and issue['resource'] == 'beds':
                actions.append(AgentAction(ActionType.ALERT, "Alert bed management - high occupancy", 3,
                              requires_approval=False, auto_executed=self.autonomous_mode))
            elif issue_type == 'capacity_critical' and issue['resource'] == 'icu':
                actions.append(AgentAction(ActionType.ALERT, "URGENT: ICU critical", 5,
                              requires_approval=False, auto_executed=True))
            elif issue_type == 'staffing_shortage':
                actions.append(AgentAction(ActionType.STAFF_CALL, "Emergency staff callback", 4,
                              requires_approval=not self.autonomous_mode))
            elif issue_type == 'equipment_critical':
                actions.append(AgentAction(ActionType.SUPPLY_ORDER, "Request emergency ventilators", 5,
                              requires_approval=True, details={'quantity': 5}))
            elif issue_type == 'environmental_alert':
                actions.append(AgentAction(ActionType.ALERT, f"Environmental: {issue['message']}", 2,
                              requires_approval=False, auto_executed=True))
            elif issue_type == 'disease_surge':
                actions.append(AgentAction(ActionType.PROTOCOL_ACTIVATION, "Consider flu surge protocol", 3,
                              requires_approval=True))
            elif issue_type == 'trend_alert':
                actions.append(AgentAction(ActionType.ALERT, "Trend alert: Rapid admission increase", 3,
                              requires_approval=False, auto_executed=True))
        actions.sort(key=lambda x: x.priority, reverse=True)
        self._add_thought("PLANNING", f"Generated {len(actions)} actions", "Issue-to-action mapping",
                         f"Top: {actions[0].description if actions else 'None'}", 0.80)
        return actions

    def execute(self, actions: List[AgentAction]) -> Dict[str, Any]:
        executed, pending = [], []
        for action in actions:
            if action.auto_executed or (self.autonomous_mode and not action.requires_approval):
                action.auto_executed = True
                action.outcome = "Executed automatically"
                executed.append(action)
                self.actions_taken.append(action)
                AGENT_LOG.append({'timestamp': datetime.now().isoformat(), 'action': action.description,
                                 'type': action.action_type.value, 'auto': True})
            else:
                pending.append(action)
                self.pending_actions.append(action)
        self._add_thought("EXECUTION", f"Executed {len(executed)}, pending {len(pending)}",
                         "Autonomy-based execution", "Complete", 0.90)
        return {'executed': executed, 'pending': pending, 'total_actions': len(actions)}

    def run_cycle(self, df) -> Dict[str, Any]:
        self.reasoning_chain = []
        situation = self.perceive(df)
        issues = self.reason()
        actions = self.plan(issues)
        results = self.execute(actions)
        AGENT_MEMORY['past_predictions'].append({'timestamp': datetime.now().isoformat(),
                                                  'situation': situation, 'issues': len(issues)})
        return {'situation': situation, 'issues': issues, 'actions': results,
                'reasoning_chain': [self._thought_to_dict(t) for t in self.reasoning_chain]}

    def get_ai_analysis(self, df) -> str:
        situation = self.current_situation or self.perceive(df)
        issues = self.reason()
        if not GEMINI_AVAILABLE:
            return self._generate_fallback_analysis(situation, issues)
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""Hospital Status ({self.hospital_name}):
- Bed: {situation['metrics']['bed_occupancy']}%, ICU: {situation['metrics']['icu_occupancy']}%
- Staff Ratio: {situation['metrics']['staff_ratio']}, AQI: {situation['environment']['pollution_aqi']}
Issues: {len(issues)}
Provide: 1) Assessment 2) Top 3 actions 3) 24h outlook. Be concise."""
            response = model.generate_content(prompt)
            return response.text
        except:
            return self._generate_fallback_analysis(situation, issues)

    def _generate_fallback_analysis(self, situation: Dict, issues: List) -> str:
        metrics = situation.get('metrics', {})
        bed_occ = metrics.get('bed_occupancy', 0)
        status = "🔴 CRITICAL" if bed_occ >= 90 else "🟡 ELEVATED" if bed_occ >= 75 else "🟢 STABLE"
        return f"""## Status: {status}
- Beds: {bed_occ}% ({metrics.get('available_beds', 0)} available)
- ICU: {metrics.get('icu_occupancy', 0)}%
- Issues: {len(issues)}
"""

    def _add_thought(self, step: str, observation: str, reasoning: str, conclusion: str, confidence: float):
        self.reasoning_chain.append(AgentThought(step, observation, reasoning, conclusion, confidence))

    def _thought_to_dict(self, thought: AgentThought) -> Dict:
        return {'step': thought.step, 'observation': thought.observation, 'reasoning': thought.reasoning,
                'conclusion': thought.conclusion, 'confidence': thought.confidence, 'timestamp': thought.timestamp.isoformat()}

    def get_reasoning_trace(self) -> str:
        trace = "## Agent Reasoning\n"
        for i, t in enumerate(self.reasoning_chain, 1):
            trace += f"**{i}. {t.step}**: {t.conclusion} ({t.confidence:.0%})\n"
        return trace

    def approve_action(self, index: int) -> bool:
        if 0 <= index < len(self.pending_actions):
            action = self.pending_actions.pop(index)
            action.outcome = "Approved"
            self.actions_taken.append(action)
            AGENT_LOG.append({'timestamp': datetime.now().isoformat(), 'action': action.description,
                             'type': action.action_type.value, 'approved': True})
            return True
        return False

    def reject_action(self, index: int) -> bool:
        if 0 <= index < len(self.pending_actions):
            action = self.pending_actions.pop(index)
            AGENT_LOG.append({'timestamp': datetime.now().isoformat(), 'action': action.description,
                             'type': action.action_type.value, 'approved': False})
            return True
        return False


def get_agent_log() -> List[Dict]:
    return AGENT_LOG

def get_agent_memory() -> Dict:
    return AGENT_MEMORY
