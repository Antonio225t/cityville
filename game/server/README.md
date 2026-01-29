# Cityville Preservation Project

Welcome back to Cityville! This project lets you relive the classic 2011 experience, just as it was at its peak popularity.

Please note that this is project is still in development and features added in later years are not currently supported, 
and some assets may be missing. In addition, features that require neighbors and requests are not currently implemented.

This guide provides the steps to set up and run the Cityville server on your local machine.

### 1. Prerequisites

Before you begin, ensure you have the following installed on your system:

*   **Python 3:** The server is built on Python.
*   **Flash-Capable Web Browser:** Required to play the game.
    *   **Note:** Adobe Flash is no longer supported by most modern browsers. 
    
### 2. Setup

1.  **Arrange Files:**
    Create a main project folder. Inside it, place the server files in a directory named `server` and the client/game assets in a directory named `client`. The structure should look like this:

    ```
    cityville/
    +-- client/       <-- Place game assets here
    +-- server/       <-- Place server files here
    ```

2.  **Install Dependencies:**
    Open a terminal or command prompt, navigate into the `server` directory, and run the following command to install the required packages:

    ```
    pip install -r requirements.txt
    ```

### 3. Migrating Existing Data (Optional)

If you are moving an existing installation, you can migrate your user data. Copy the user folder (333) from your old `users` directory and place it into the `server/users` directory of your new setup.

### 4. Running the Game

1.  **Start the Server:**
    *   **On Windows:** Run the batch file:
        ```
        run_server.bat
        ```
    *   **On macOS/Linux:** Use the Flask command from the server directory:
        ```
        flask run
        ```

2.  **Play the Game:**
    Once the server is running, open your Flash-capable web browser and go to: `http://localhost:5000/`