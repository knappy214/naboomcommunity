#!/bin/bash

# MQTT Service Monitoring Script
# This script monitors the MQTT service and provides health checks and alerting

set -euo pipefail

# Configuration
MQTT_SERVICE_NAME="naboom-gunicorn"  # The main service that includes MQTT
MQTT_HEALTH_URL="http://localhost:8000/api/mqtt/health/"
MQTT_METRICS_URL="http://localhost:8000/api/mqtt/metrics/"
LOG_FILE="/var/log/naboom/mqtt_monitor.log"
ALERT_EMAIL="${ALERT_EMAIL:-admin@naboomcommunity.com}"
MAX_RETRIES=3
RETRY_DELAY=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error logging function
log_error() {
    echo -e "${RED}$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

# Warning logging function
log_warning() {
    echo -e "${YELLOW}$(date '+%Y-%m-%d %H:%M:%S') - WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Success logging function
log_success() {
    echo -e "${GREEN}$(date '+%Y-%m-%d %H:%M:%S') - SUCCESS: $1${NC}" | tee -a "$LOG_FILE"
}

# Check if MQTT health endpoint is responding
check_mqtt_health() {
    local retries=0
    local response=""
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if response=$(curl -s -w "%{http_code}" -o /tmp/mqtt_health_response.json "$MQTT_HEALTH_URL" 2>/dev/null); then
            local http_code="${response: -3}"
            if [ "$http_code" = "200" ] || [ "$http_code" = "503" ]; then
                # Parse the response
                local status=$(jq -r '.status' /tmp/mqtt_health_response.json 2>/dev/null || echo "unknown")
                local connected=$(jq -r '.connected' /tmp/mqtt_health_response.json 2>/dev/null || echo "false")
                local uptime=$(jq -r '.uptime_seconds' /tmp/mqtt_health_response.json 2>/dev/null || echo "0")
                local error_count=$(jq -r '.metrics.error_count' /tmp/mqtt_health_response.json 2>/dev/null || echo "0")
                
                echo "$status|$connected|$uptime|$error_count"
                return 0
            else
                log_warning "MQTT health endpoint returned HTTP $http_code (attempt $((retries + 1))/$MAX_RETRIES)"
            fi
        else
            log_warning "Failed to connect to MQTT health endpoint (attempt $((retries + 1))/$MAX_RETRIES)"
        fi
        
        retries=$((retries + 1))
        if [ $retries -lt $MAX_RETRIES ]; then
            sleep $RETRY_DELAY
        fi
    done
    
    log_error "Failed to check MQTT health after $MAX_RETRIES attempts"
    echo "unhealthy|false|0|0"
    return 1
}

# Check if MQTT service is running
check_mqtt_service() {
    if systemctl is-active --quiet "$MQTT_SERVICE_NAME"; then
        return 0
    else
        return 1
    fi
}

# Restart MQTT service
restart_mqtt_service() {
    log "Attempting to restart MQTT service..."
    
    if systemctl restart "$MQTT_SERVICE_NAME"; then
        log_success "MQTT service restarted successfully"
        sleep 10  # Wait for service to fully start
        
        # Verify service is running
        if check_mqtt_service; then
            log_success "MQTT service is running after restart"
            return 0
        else
            log_error "MQTT service failed to start after restart"
            return 1
        fi
    else
        log_error "Failed to restart MQTT service"
        return 1
    fi
}

# Send alert email
send_alert() {
    local subject="$1"
    local message="$2"
    
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null || true
    fi
    
    # Also log the alert
    log_error "ALERT: $subject - $message"
}

# Main monitoring function
monitor_mqtt() {
    log "Starting MQTT service monitoring..."
    
    # Check if service is running
    if ! check_mqtt_service; then
        log_error "MQTT service is not running"
        send_alert "MQTT Service Down" "The MQTT service is not running. Attempting to restart..."
        
        if restart_mqtt_service; then
            send_alert "MQTT Service Restarted" "The MQTT service has been successfully restarted."
        else
            send_alert "MQTT Service Restart Failed" "Failed to restart the MQTT service. Manual intervention required."
            return 1
        fi
    fi
    
    # Check MQTT health
    local health_data
    if health_data=$(check_mqtt_health); then
        IFS='|' read -r status connected uptime error_count <<< "$health_data"
        
        log "MQTT Health Check - Status: $status, Connected: $connected, Uptime: ${uptime}s, Errors: $error_count"
        
        # Check for unhealthy status
        if [ "$status" = "unhealthy" ]; then
            log_error "MQTT service is unhealthy"
            send_alert "MQTT Service Unhealthy" "The MQTT service is reporting as unhealthy. Status: $status, Connected: $connected"
            
            # Attempt restart
            if restart_mqtt_service; then
                send_alert "MQTT Service Restarted" "The MQTT service has been restarted due to unhealthy status."
            else
                send_alert "MQTT Service Restart Failed" "Failed to restart the unhealthy MQTT service."
                return 1
            fi
        elif [ "$status" = "degraded" ]; then
            log_warning "MQTT service is degraded"
            send_alert "MQTT Service Degraded" "The MQTT service is reporting as degraded. Status: $status, Errors: $error_count"
        elif [ "$status" = "healthy" ]; then
            log_success "MQTT service is healthy"
        fi
        
        # Check for high error count
        if [ "$error_count" -gt 10 ]; then
            log_warning "High error count detected: $error_count"
            send_alert "MQTT High Error Count" "The MQTT service has a high error count: $error_count"
        fi
        
        # Check for disconnection
        if [ "$connected" = "false" ]; then
            log_warning "MQTT client is not connected to broker"
            send_alert "MQTT Client Disconnected" "The MQTT client is not connected to the broker."
        fi
        
    else
        log_error "Failed to check MQTT health"
        send_alert "MQTT Health Check Failed" "Failed to check MQTT service health. The service may be down."
        return 1
    fi
    
    return 0
}

# Get MQTT metrics
get_mqtt_metrics() {
    if curl -s "$MQTT_METRICS_URL" > /tmp/mqtt_metrics.json 2>/dev/null; then
        log "MQTT Metrics retrieved successfully"
        cat /tmp/mqtt_metrics.json
    else
        log_error "Failed to retrieve MQTT metrics"
        return 1
    fi
}

# Main script logic
main() {
    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Check if jq is installed
    if ! command -v jq >/dev/null 2>&1; then
        log_error "jq is required but not installed. Please install jq to use this monitoring script."
        exit 1
    fi
    
    # Check if curl is installed
    if ! command -v curl >/dev/null 2>&1; then
        log_error "curl is required but not installed. Please install curl to use this monitoring script."
        exit 1
    fi
    
    case "${1:-monitor}" in
        "monitor")
            monitor_mqtt
            ;;
        "health")
            check_mqtt_health
            ;;
        "metrics")
            get_mqtt_metrics
            ;;
        "restart")
            restart_mqtt_service
            ;;
        "status")
            if check_mqtt_service; then
                echo "MQTT service is running"
                check_mqtt_health
            else
                echo "MQTT service is not running"
                exit 1
            fi
            ;;
        *)
            echo "Usage: $0 {monitor|health|metrics|restart|status}"
            echo "  monitor  - Run full monitoring check (default)"
            echo "  health   - Check MQTT health status"
            echo "  metrics  - Get MQTT metrics"
            echo "  restart  - Restart MQTT service"
            echo "  status   - Check service status"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
