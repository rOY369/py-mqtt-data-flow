# PY-MQTT-DATA-FLOW

## Overview

This MQTT Message Processing Framework is a highly scalable, modular, and extensible system designed for efficient processing of MQTT messages in IoT applications. Built in Python and utilizing the Paho MQTT library, it enables applications to configure multiple MQTT clients, employ a queue-based approach for message handling, define custom callbacks based on message content, and integrate a library of processing functionalities.

## Features

- Scalable Message Processing: Efficiently process a large number of MQTT messages.
Extensible Design: Easily add more callbacks, message processors, and functionalities.
Modular and Configurable: Flexible configuration to suit various Python applications.
Support for Multiple MQTT Clients: Configure and manage communications with multiple MQTT brokers.

- Queue-Based Approach: Ensure orderly processing of incoming messages.
Custom Callbacks: Execute specific logic based on message topic and payload.

- Error Resilience: Isolate and log callback errors to maintain process integrity.
Predefined Processors: Leverage and configure built-in processors for common tasks such as message relaying and formatting.

- Installation
To install the MQTT Message Processing Framework, ensure you have Python 3.6+ and pip installed on your system. Then run the following command

`pip install mqtt-message-processing-framework`

## Quick Start

Create a Configuration File: Define your MQTT clients, topics, rules, and processing chains in a YAML configuration file. See Configuration for details.

Write Custom Callbacks: Implement any custom logic in Python modules referenced in your configuration file.

Run the Framework:

## Configuration

The framework's behavior is driven by a YAML configuration file.

```
# MQTT Clients Configuration
# Define all MQTT clients along with the topics they subscribe to.
mqtt_clients:
  - client_id: "client1"
    broker_url: "mqtt://example.com"
    port: 1883
    topics:
      - name: "/sensors/temperature"
        qos: 1
      - name: "/sensors/humidity"
        qos: 1

# Callbacks Definition
# Centralized section for defining callback functions for both simple and complex processing.
callbacks:
  handle_temperature_alert:
    module: "temperature_alerts.py"
    function: "alert_if_high"
  handle_humidity_analysis:
    module: "humidity_analysis.py"
    function: "analyze_humidity"
  sample_temperature_collection:
    module: "sampler_processor.py"
    function: "handle_temperature_sample"
  process_sampled_temperature:
    module: "temperature_processor.py"
    function: "handle_processed_temperature"

# Rules Configuration
# Rules can specify a direct callback for simple tasks or an action referring to a processing chain.
rules:
  # Simple callback rule for temperature alerts
  - rule: "simple_temperature_alert"
    source_client_id: "client1"
    topic: "/sensors/temperature"
    callback: "handle_temperature_alert"
    execution_mode: "sequential"
  
  # Simple callback rule for humidity analysis
  - rule: "simple_humidity_analysis"
    source_client_id: "client1"
    topic: "/sensors/humidity"
    callback: "handle_humidity_analysis"
    execution_mode: "sequential"
  
  # Complex processing chain for temperature data sampling and processing
  - rule: "temperature_sampling_and_processing"
    source_client_id: "client1"
    topic: "/sensors/temperature"
    action: "temperature_sampling_and_processing_chain"
    execution_mode: "threaded"

# Processing Chains Configuration
# Defines the sequence of processing steps for complex scenarios.
processing_chains:
  temperature_sampling_and_processing_chain:
    # Sampler step: collects messages over a specified duration.
    - step: "sampler"
      config:
        duration: 60  # in seconds
        callback: "sample_temperature_collection"
    
    # Custom processor step: processes the sampled data.
    - step: "custom_processor"
      config:
        callback: "process_sampled_temperature"
    
    # Relay step: demonstrates using a predefined processor to relay messages.
    # This step is configurable to relay messages to another MQTT topic or client.
    - step: "relay"
      config:
        target_client_id: "client2"
        target_topic: "/processed/temperature"
```

### Key Configuration Elements Explained:

- **mqtt_clients**: This section lists all MQTT clients that the framework will connect to. For each client, you specify the client_id, broker_url, port, and a list of topics to subscribe to.

- **callbacks**: Defines the callbacks available for use in the framework. These can be simple functions for direct message processing or part of a more complex processing chain. Each callback is associated with a module and function name.

- **rules**: Lists the rules that determine how messages are processed. A rule can directly invoke a callback based on a message's topic (and optionally, other conditions) or trigger a more complex processing chain. The execution_mode specifies how the framework should handle message processing (sequentially or in parallel).

- **processing_chains**: Details the steps involved in processing chains for complex message handling scenarios. Each step in a chain can perform different actions, such as sampling data over time, processing collected data, or relaying data to another topic/client.

- **step**: "relay": This demonstrates how to use a predefined processor from the library to forward messages to another topic or client, highlighting the relay mechanism's configuration.

## Documentation

For further details on installation, configuration, and development, please refer to the docs directory. Here you will find comprehensive guides and API documentation to help you get started.

## Contributing

We welcome contributions from the community! If you'd like to contribute, please follow these steps:

- Fork the Repository: Make a copy of the project to your GitHub account.
- Create a Feature Branch: Work on your feature or fix in a separate branch.
- Submit a Pull Request: Once your feature is ready and tested, submit a PR for review.

For more information on making contributions, please read CONTRIBUTING.md.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions, please file an issue on the GitHub issue tracker.