# The ICC Digital ID Manager

The ICC Digital ID Manager is a Python/Django application for the [Hyperledger Aries Cloud Agent Python (aca-py)](https://github.com/hyperledger/aries-cloudagent-python).
The ID Manager plays the role of an issuer in a self-sovereign Digital Identity ecosystem, and it is expecting to issue credentials to a [Mobile Digital ID wallet](https://vonx.io/getwallet).

Functionalities include:
- Create a Schema
- Create a Credential Definition
- Obtain credentials with a credential request
- Verify credentials

Pre-Requisites
* [Docker](https://www.docker.com/products/docker-desktop)

* [ngrok](https://ngrok.com/)

## Demo of the ICC Digital ID Manager

This demo uses the [British Columbia Vonx Test Blockchain](http://test.bcovrin.vonx.io). However, the ID Manager can be connected to your own blockchain.

1. Clone this repository
1. Start ngrok from terminal
    ```
    ngrok http 8002
    ```
1. Open a bash terminal in the /demo-public folder
1. Copy the http url generated by ngrok  and export it like so:
    ```
    export SITE_URL=http://12345678.ngrok.io
    ```
1. Run
    ```
    docker-compose up -d
    ```
2. Check out the ID Manager API documentation [http://localhost:8082/swagger/](http://localhost:8082/swagger/)
3. Check out the Agent API documentation [http://localhost:4002/api/doc](http://localhost:4002/api/doc)
4. Create a user
    ```
    docker exec -it demo-public_id-manager_1 python manage.py createsuperuser
    ```
5. Log in with your new user at [http://localhost:8082/admin/](http://localhost:8082/admin/)
6. Create an admin user token 
    - Click on the `+ Add` button next to Tokens
    - Select your user
    - Click `Save`
    - Copy the `Key` displayed, it is a long sequence of letters and numbers

## Create an invitation for a Digital ID user
Now you may choose whether to continue the tutorial in the admin view [http://localhost:8082/admin/](http://localhost:8082/admin/) or requesting a credential with code calling the ID Manager


## Option A: Create an invitation with scripts
You may inspect the scripts with `vim` or any tool of your choice so you can see how the ID Manager could be called from your system. Take note of `demo\demo-credential-request.sh` which reflects how your system could call the ID Manager to create credentials for a user.

Stay in your terminal

1. Set your authorization token, replacing the string with your token
    ```
    export DEMO_TOKEN=e5f405fa4747742595a9a49c4ce79cfa18319d8a
    ```
2. Create a Credential Request
    ```
    chmod +x demo-run.sh
    chmod +x demo-create-schema.sh
    chmod +x demo-credential-request.sh
    chmod +x demo-create-credential-definition.sh
    ./demo-run.sh
    ```
    - The response will look something like this:
    ```
    {
        "code":"a2c95d09-efa3-4c67-aaac-c0d0bb747ccc",
        "invitation_url":"http://localhost:8082/credential-obtain?code=a2c95d09-efa3-4c67-aaac-c0d0bb747ccc"
    }
    ```
    - Copy the `invitation_url` shown and paste it into your browser
    - You should see a QR Code and text saying "Please, scan this QR code with the UN Digital ID app:", and the invitation will time out after some time

To rerun the script, it is necessary to increment the "schema" field in the `demo-public\demo-create-credential-definition.sh` as the schema will increment by 1.


## Option B: Create an invitation from the admin view 
Stay at [http://localhost:8082/admin/](http://localhost:8082/admin/)

1. Create a Schema in the Schemas section of the admin. Example:
    - name: (choose a name)
    - schema_id: (leave it blank, will be filled when uploaded to Blockchain)
    - creator: (select the creator user for the schema)
    - schema_json: 
    ```
    {
    "schema_version": "1.0",
    "schema_name": "prefs",
    "attributes": [
        "score"
    ]
    }
    ```
    *Click 'Save and continue editing' and, after that, 'Upload to Blockchain'* 
    ``

2. Create a Credential Definition in the Credential Definitions section of the admin (the `schema_id` must match one of your existing Schema's). Example:

    - name: (choose a unique name)
    - credential_id: (leave it blank, will be filled when uploaded to Blockchain)
    - creator: (select the creator user for the schema)
    - schema: (select one)
    
    *Click 'Save and continue editing' and, after that, 'Upload to Blockchain'*

3. Create a Credential Request in the Credential Requests section of the admin (the `schema_id` must match one of your existing Schema's). Example:

    - Credential definition: (choose a credential created prior to this)
    - creator: (select the creator user for the schema)
    - credential_data:
    ```
    {
    "score": "10",
    }
    ```
    - email: (the recipient's email address)

    
    *Click 'Save'

    - Copy the `Invitation URL` shown and paste it into your browser
    - You should see a QR Code and text saying "Please, scan this QR code with the UN Digital ID app:", and the invitation will time out after some time

4. Alternatively, launch a POST request from terminal like so, replacing `credential_definition` with the credential_id of the Credential Definition we created before. Replace the string `e5f405fa4747742595a9a49c4ce79cfa18319d8a` with the token you created earlier in the demo:
   
    ```
    curl --location --request POST 'http://localhost:8082/credential-request' \
    --header 'Authorization: token e5f405fa4747742595a9a49c4ce79cfa18319d8a' \
    --header 'Content-Type: application/json' \
    --data-raw '{
        "credential_definition": "Th7MpTaRZVRYnPiabds81Y:3:CL:41577:idmanagerdemocreddef",
        "email": "your_email@mail.com",
        "credential_data": "{ \"score\": \"10\" }"
    }'
    ```
    - Copy the `invitation_url` shown and paste it into your browser
    - You should see a QR Code and text saying "Please, scan this QR code with the UN Digital ID app:", and the invitation will time out after some time

## "Invitation" emails

Each time a user requests a credential an "invitation" email is created and queued for onward processing.
In order to effectively sent out all the queued emails, you must launch the sending processing.

In order to do so, enter the following command in the terminal:

```bash
docker exec -it demo-public_id-manager_1 python manage.py send_queued_mail
```

Now the console will show the result of the sending process and you should be able to check out the sent emails in Maildev (https://localhost:1080) 