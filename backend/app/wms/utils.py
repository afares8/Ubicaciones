import uuid
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

def generate_idempotency_key() -> str:
    """Generate a unique idempotency key"""
    return str(uuid.uuid4())

def hash_payload(payload: Dict[Any, Any]) -> str:
    """Create a hash of the payload for audit logging"""
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(payload_str.encode()).hexdigest()

def parse_bin_pattern(pattern: str) -> Dict[str, Any]:
    """Parse bin generation pattern like SEC{01-03}-AIS{01-10}-RK{01-05}-LV{01-04}-BIN{01-30}"""
    import re
    
    parts = pattern.split('-')
    parsed_parts = []
    
    for part in parts:
        match = re.match(r'([A-Z]+)\{(\d+)-(\d+)\}', part)
        if match:
            prefix, start, end = match.groups()
            parsed_parts.append({
                'prefix': prefix,
                'start': int(start),
                'end': int(end),
                'format_width': len(start)
            })
        else:
            parsed_parts.append({
                'prefix': part,
                'start': None,
                'end': None,
                'format_width': 0
            })
    
    return {'parts': parsed_parts}

def generate_bin_codes(pattern: str) -> list:
    """Generate all bin codes from a pattern"""
    parsed = parse_bin_pattern(pattern)
    codes = []
    
    def generate_recursive(parts, current_code=""):
        if not parts:
            codes.append(current_code.strip('-'))
            return
        
        part = parts[0]
        remaining = parts[1:]
        
        if part['start'] is not None:
            for i in range(part['start'], part['end'] + 1):
                formatted_num = str(i).zfill(part['format_width'])
                new_code = f"{current_code}-{part['prefix']}{formatted_num}" if current_code else f"{part['prefix']}{formatted_num}"
                generate_recursive(remaining, new_code)
        else:
            new_code = f"{current_code}-{part['prefix']}" if current_code else part['prefix']
            generate_recursive(remaining, new_code)
    
    generate_recursive(parsed['parts'])
    return codes

def validate_warehouse_code(whs_code: str) -> bool:
    """Validate warehouse code format"""
    return len(whs_code) <= 8 and whs_code.isalnum()

def format_audit_log(action: str, user: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
    """Format audit log entry"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "user_name": user,
        "action": action,
        "payload": json.dumps(payload) if payload else None,
        "payload_hash": hash_payload(payload) if payload else None
    }

def safe_decimal_conversion(value: Any, default: float = 0.0) -> float:
    """Safely convert value to decimal/float"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        logger.warning(f"Could not convert {value} to decimal, using default {default}")
        return default
