# Instructions to run the project


# Clone o repositório
 ```bash
git clone https://github.com/GustavoGarciaPereira/SIESTA_Platform.git
 ```
## entre na pasta principal do projeto
```bash
cd SIESTA_Platform
```

## With Docker

1.  **Build the Docker image:**
    ```bash
    docker-compose build
    ```
2.  **Run the project:**
    ```bash
    docker-compose up
    ```
3.  Access the application at [http://localhost:8000](http://localhost:8000).

## Without Docker

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```
2.  **Activate the virtual environment:**
    -   On Linux/macOS:
        ```bash
        source venv/bin/activate
        ```
    -   On Windows:
        ```bash
        venv\Scripts\activate
        ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run database migrations:**
    ```bash
    python manage.py migrate
    ```
5.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```
6.  Access the application at [http://localhost:8000](http://localhost:8000).
