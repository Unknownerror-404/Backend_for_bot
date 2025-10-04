# Backend_for_bot

## How to download and use:

#Documentation: 
1] Training the rasa model and setup to create a local server.

To use this instance of rasa, install rasa and rasa.sdk from the requirements.txt file.
Initially make sure all files have been installed properly and setup the structrue correctly as:

main_directory/
│
├── config.yml
├── credentials.yml
├── domains.yml
├── endpoints.yml
│
├── data/
│   ├── nlu.yml
│   ├── rules.yml
│   └── stories.yml
│
├── front-end/
│   ├── app.py
│   ├── static/
│   │   ├── css/
│   │   │   ├── health.css
│   │   │   ├── logged_in_health.css
│   │   │   ├── style_aboutus.css
│   │   │   ├── style_chat.css
│   │   │   ├── style_createacc.css
│   │   │   └── style_loginpage.css
│   │   └── images/
│   │       ├── bg.jpg
│   │       ├── blurred_bg.jpg
│   │       └── healthcare.jpg
│   └── templates/
│       ├── aboutus.html
│       ├── chat_logged_in.html
│       ├── chat.html
│       ├── createacc.html
│       ├── index.html
│       ├── loginpage.html
│       └── logged_in_index.html
│
├── models/
│   └── _some_model.tar
│
└── tests/
    └── test_stories.yml


struture your directory as shown above:

Ensure you have a python version from 3.8 to 3.11 as rasa is incompatible with recent 3.11 > versions.
For convinience do python --version or python3 --version in your terminal (Windows).
After ensure you have a compatible version most favourably python 3.11, install the following packages from  requirements.txt
=============== required packages ===================
rasa
rasa.sdk
==================++++++++++++========================

Upon completion, ensure you've located the correct directory and structure as well, change your current directroy to the main_directory as mentioned above.
and perform the following commands:

===================== cmd prompt ========================
> rasa train
> // store the result in the models subdirectory as shown above.
> rasa run --enable-api --cors="*"  --debug
> // this will run the recently trained rasa model on an output port mostly preferably local-host//server.

===================== cmd prompt ========================


2] Creating a sql server:

After creating the rasa server, to access all features from our website please go to the following link:
https://www.microsoft.com/en-in/sql-server/sql-server-downloads/

scroll down a bit and ensure that you download sql server express 2022. 
Move onto installation selecting a basic server configuration when prompted.
upon completion, close out of the setup, and go to your local cmd prompt to perform sql cmommands on it, type the following:

======================= cmd prompt ============================
> sqlcmd -S .\SQLEXPRESS -E
================== end of cmd prompt ===========================



======================= sqlcmd prompt =========================
> CREATE DATABASE model;
> GO
> // This will create a sql database named model, which can be used as:
> USE model
> GO
> //Then create the follwing tables which are required to store user login info and chat session infos for dynamic data loading. 
> CREATE TABLE Users (
>    UserID INT IDENTITY(1,1) PRIMARY KEY,
>    Email NVARCHAR(255) NOT NULL,
>    PasswordHash NVARCHAR(255) NOT NULL,
>    CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),
>    person_name NVARCHAR(100) NOT NULL
> ); 
> //Creating user data storage, currently prototype form.
> CREATE TABLE ChatSessions (
>    Id INT IDENTITY(1,1) PRIMARY KEY,
>    UserId INT NOT NULL,
>    Session_Id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
>    Session_Title NVARCHAR(255) NULL,
>    User_Chat NVARCHAR(MAX) NULL,
>    Bot_Chat NVARCHAR(MAX) NULL,
>    CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),
>    CONSTRAINT FK_Chat_User FOREIGN KEY (UserId) REFERENCES Users(UserID)
> );
 ======================= sqlcmd prompt =========================

This should create the required sql tables to work properly with the remaining code.

3] Creating a local host-server for testing using app.py
Once you have the rasa and sql servers up and running, go to your code editor, and execute the app.py file from this repo, 
e.g. if you are using vs code, go to your working directory, and play the python script with python app.py.

This should redirect you to a site which provide a glimpse at our clinical chatbot.
