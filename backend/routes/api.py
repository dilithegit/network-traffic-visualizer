from flask import Blueprint, jsonify, request
from capture.interface_manager import (
    get_interface_list,
    get_interface_details,
    set_active_interface,
    get_active_interface_display,
)
from capture.sniffer import start_capture, stop_capture, is_capture_running, traffic_data
from analysis.stats import get_traffic_stats
from analysis.spike_detector import spike_detector
from alerts.notifier import alert_notifier

api = Blueprint('api', __name__)


@api.route('/interfaces', methods=['GET'])
def interfaces():
    """Return available capture interfaces plus their health status (req 5)."""
    return jsonify({
        'interfaces': get_interface_list(),
        'statuses': get_interface_details(),
        'active_interface': get_active_interface_display(),
    }), 200


@api.route('/sensitivity', methods=['GET'])
def get_sensitivity_route():
    """Return the current spike-detection sensitivity level."""
    return jsonify({'sensitivity': spike_detector.get_sensitivity()}), 200


@api.route('/sensitivity', methods=['POST'])
def set_sensitivity_route():
    """Change the spike-detection sensitivity (low | medium | high)."""
    data = request.get_json(force=True, silent=True) or {}
    level = data.get('level')
    ok = spike_detector.set_sensitivity(level) if level else False
    return jsonify({'ok': ok, 'sensitivity': spike_detector.get_sensitivity()}), 200 if ok else 400


@api.route('/capture/start', methods=['POST'])
def start_capture_route():
    """Start capture on a selected interface."""
    data = request.get_json(force=True, silent=True) or {}
    interface = data.get('interface')
    if not interface:
        return jsonify({'success': False, 'error': 'Interface name is required'}), 400

    started = start_capture(interface)
    return jsonify({'success': started, 'running': started, 'active_interface': get_active_interface_display()}), 200 if started else 500


@api.route('/capture/stop', methods=['POST'])
def stop_capture_route():
    """Stop the packet capture."""
    stopped = stop_capture()
    return jsonify({'success': stopped, 'running': not stopped}), 200 if stopped else 500


@api.route('/capture/status', methods=['GET'])
def capture_status_route():
    """Return the current capture running state."""
    return jsonify({'running': is_capture_running(), 'active_interface': get_active_interface_display()}), 200


@api.route('/traffic', methods=['GET'])
def get_traffic():
    """Provide the most recent packet traffic entries."""
    recent = list(traffic_data)[-100:]
    return jsonify(recent), 200


@api.route('/stats', methods=['GET'])
def stats_route():
    """Return traffic and bandwidth statistics."""
    return jsonify(get_traffic_stats()), 200


@api.route('/alerts', methods=['GET'])
def get_alerts():
    """Return recent alerts, URL extraction history, and suspicious host data."""
    return jsonify({
        'alerts': alert_notifier.get_recent_alerts(),
        'url_history': alert_notifier.get_recent_urls(),
        'suspicious_hosts': alert_notifier.get_suspicious_ips(),
    }), 200
