# RR-Team-36-Distributed-Load-Testing-System

## Setup
1. Start ZooKeeper and Kafka:
    ```bash
    sudo systemctl start kafka
    sudo systemctl status kafka
    ```

2. Run the server program:
    ```bash
    python3 server.py
    ```

3. Run the orchestrator node:
    ```bash
    python3 orchestrator.py
    ```

4. Run the frontend:
    ```bash
    python3 frontend.py
    ```
    - Choose the appropriate test type.

5. Run the driver program:
    ```bash
    python3 driver.py
    ```

## Contributing
Feel free to contribute by submitting bug reports, feature requests, or code contributions.


