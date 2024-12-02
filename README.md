# ITSUChatBot
Project Description: ITSUChatBot
ITSUChatBot is an intelligent Telegram bot designed to interact with students, applicants, and anyone interested in learning more about IT STEP University. The bot leverages modern artificial intelligence technologies and ensures effective communication through integrations with databases, Google Docs, and OpenAI.

Project Features
Query Understanding:
The bot analyzes user queries, determines relevance, and provides informative responses.

Integration with Google Docs:
Responses are based on up-to-date information retrieved from Google documents.

Logs Storage in MongoDB:
All queries and responses are stored in a database for further analysis and system improvement.

Asynchronous Query Processing:
The bot supports simultaneous interactions with multiple users.

Flexibility and Scalability:
The project is easily adaptable for new business tasks thanks to its modular architecture and use of modern technology stacks.

Technologies Used
Python: The primary programming language of the project.
Python Telegram Bot: A library for integrating with the Telegram API.
OpenAI GPT: Response generation based on artificial intelligence.
Google Docs API: Reading text from Google documents.
MongoDB: A database for storing interaction logs.
Asynchronous Processing: Utilization of asyncio for handling multiple requests concurrently.
Target Audience
ITSUChatBot is aimed at:

Students and applicants who want information about courses, programs, and admission requirements.
University staff who need a tool to automate responses to common questions.
IT professionals interested in implementing autonomous AI agents for business.
Benefits of ITSUChatBot
Ease of Use: Accessible via Telegram for quick information retrieval.
Data Accuracy: Information is updated in real-time through Google Docs integration.
Simple Setup: The project is easy to deploy on any server with the help of a requirements.txt file and detailed instructions.
High Efficiency: Asynchronous query handling allows the bot to serve many users simultaneously.
Current Project Status
The project is completed and ready for use.
The latest update includes asynchronous query processing and log storage in MongoDB.

------------------------------------------------------------------------------------

Environment Setup Instructions
Follow the steps below to set up the environment and deploy the ITSUChatBot:

1. Install Python
Ensure Python 3.8 or higher is installed on your system. You can download it from Python.org.

2. Clone the Repository
Clone the project's GitHub repository to your local machine:
bash
Copy code
git clone <repository_url>
cd <repository_name>

3. Create a Virtual Environment
Set up a virtual environment to isolate project dependencies:
bash
Copy code
python -m venv venv
Activate the virtual environment:

On Windows:
bash
Copy code
venv\Scripts\activate

On macOS/Linux:
bash
Copy code
source venv/bin/activate

4. Install Dependencies
Install all required libraries and packages using the requirements.txt file:
bash
Copy code
pip install -r requirements.txt

5. Configure API Keys
Create a .env file in the project root directory and add the following API keys:
makefile
Copy code
OPENAI_API_KEY=<Your OpenAI API Key>
TELEGRAM_BOT_TOKEN=<Your Telegram Bot Token>
MONGO_URI=<Your MongoDB URI>
GOOGLE_DOC_ID=<Google Docs ID>

6. Set Up Google Docs API
To enable the integration with Google Docs:
Go to Google Cloud Console.
Create a new project and enable the Google Docs API.
Download the credentials.json file and place it in the project root directory.

7. Run the Bot
Start the bot by running the main Python script:
bash
Copy code
python src/itsuchatbot.py

8. Test the Bot
Open Telegram, search for your bot, and interact with it to ensure it functions as expected.
