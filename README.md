# GDPR Obfuscator

This project provides a general-purpose tool to process data being ingested into AWS and intercept Personally Identifiable Information (PII). All information stored by Northcoders data projects should be for bulk data analysis only. Consequently, there is a requirement under GDPR to ensure that all data containing information that can be used to identify an individual should be anonymised.

## 🚀 Features

-   **PII Obfuscation**: Replaces sensitive data in specified fields with a `****` mask.
-   **Multi-format Support**: Handles **CSV**, **JSON**, and **Parquet** data formats.
-   **AWS S3 Integration**: Reads source files from S3 and uploads processed results back to the same bucket with a `transformed/` prefix.
-   **Flexible Invocation**:
    -   As a **command-line utility** for local execution and demonstration.
    -   As a **library module** for integration into other Python codebases.
    -   As an **AWS Lambda function**, ready for integration with AWS Step Functions, EventBridge, or Airflow.
-   **High Code Quality**: The project features extensive test coverage, adheres to PEP-8 standards, and includes static security analysis.

## ⚙️ Installation and Setup

### 1. Prerequisites

-   Python 3.9+
-   `pip` and `venv`
-   AWS CLI

### 2. Local Environment Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd gdpr-obfuscator
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install all development and testing dependencies:**
    ```bash
    pip install -r requirements-dev.txt
    ```

4.  **Configure AWS Credentials:**
    For local execution and testing, you need to configure your AWS CLI. Ensure you have appropriate permissions (`s3:GetObject`, `s3:PutObject`, `s3:HeadObject`) for the target S3 buckets.
    ```bash
    aws configure
    ```

## 💻 Usage

### Command-Line Execution

You can run the obfuscation process locally by passing parameters as a JSON string.

```bash
# Example for CSV
python -m src.main '{"file_to_obfuscate": "s3://your-bucket/your-file.csv", "pii_fields": ["name", "email"]}'

# Example for JSON
python -m src.main '{"file_to_obfuscate": "s3://your-bucket/your-file.json", "pii_fields": ["name", "email"]}'

# Example for Parquet
python -m src.main '{"file_to_obfuscate": "s3://your-bucket/your-file.parquet", "pii_fields": ["name", "email"]}'
```

### Library Usage

You can import and use the core logic within your Python code.

```python
import boto3
from src.s3_utils import obfuscate_data

s3_client = boto3.client("s3")
params = {
    "file_to_obfuscate": "s3://your-bucket/your-file.csv",
    "pii_fields": ["name", "email"]
}

# Get the result as bytes
obfuscated_bytes = obfuscate_data(params, s3_client, return_bytes=True)

# Or perform the full cycle with S3 upload and get metadata
result_summary = obfuscate_data(params, s3_client, return_bytes=False)
print(result_summary)
```

## ☁️ Deployment to AWS Lambda

1.  **Create a Deployment ZIP Archive:**
    This archive will contain your code and all production dependencies.
    ```bash
    # Install dependencies into a 'package' directory
    pip install -r requirements.txt -t ./package
    
    # Copy your source code
    cp -r src/* ./package/
    
    # Create the ZIP archive
    cd package
    zip -r ../deployment_package.zip .
    cd ..
    ```

2.  **Create the Lambda Function in AWS:**
    -   **Function Name**: `gdpr-obfuscator`
    -   **Runtime**: Python 3.9 (or newer)
    -   **Architecture**: x86_64
    -   **Handler**: `lambda_handler.lambda_handler`
    -   **Code Upload**: Upload the created `deployment_package.zip`.
    -   **IAM Role**: Create or use an existing role with `s3:GetObject`, `s3:PutObject`, and `s3:HeadObject` permissions for the S3 buckets your function will interact with.
    -   **Timeout**: Set an adequate execution timeout (e.g., 1 minute).

3.  **Example Invocation via AWS Step Functions:**
    You can integrate this Lambda into an AWS Step Function. An example command for starting an execution:
    ```bash
    aws stepfunctions start-execution \
      --state-machine-arn "arn:aws:states:eu-west-2:645583760702:stateMachine:InvokeLambdaAndRetrieveFile" \
      --input '{"file_to_obfuscate": "s3://gdpr-ingestion-bucket/uk_student_records_1000.parquet", "pii_fields": ["name", "email_address"]}'
    ```

## 🧪 Testing and Code Quality

### Running Tests

To run the full test suite:
```bash
pytest
```

To view the code coverage report:
```bash
pytest --cov=src
```

### Static Security Analysis

The project uses `bandit` to scan for common security vulnerabilities in the code.
```bash
bandit -r src/
```
## 🚀 Возможности

aws stepfunctions start-execution --state-machine-arn "arn:aws:states:eu-west-2:645583760702:stateMachine:InvokeLambdaAndRetrieveFile" --input '{"file_to_obfuscate": "s3://gdpr-ingestion-bucket/uk_student_records_1000.csv", "pii_fields": ["name", "email_address"]}'
- **Обфускация PII**: Заменяет конфиденциальные данные в указанных полях на маску `****`.
- **Поддержка нескольких форматов**: Работает с файлами **CSV**, **JSON** и **Parquet**.
- **Интеграция с AWS S3**: Читает исходные файлы из S3 и загружает обработанные результаты обратно в тот же бакет с префиксом `transformed/`.
- **Гибкие способы вызова**:
  - Как **командная утилита** для локального запуска и демонстрации.
  - Как **библиотечный модуль** для интеграции в другие Python-проекты.
  - Как **AWS Lambda функция**, готовая к интеграции с AWS Step Functions, EventBridge или Airflow.
- **Высокое качество кода**: Проект имеет обширное тестовое покрытие, соответствует стандарту PEP-8 и включает статический анализ безопасности.

aws stepfunctions start-execution --state-machine-arn "arn:aws:states:eu-west-2:645583760702:stateMachine:InvokeLambdaAndRetrieveFile" --input '{"file_to_obfuscate": "s3://gdpr-ingestion-bucket/uk_student_records_1000.json", "pii_fields": ["name", "email_address"]}'
## ⚙️ Установка и настройка

aws stepfunctions start-execution --state-machine-arn "arn:aws:states:eu-west-2:645583760702:stateMachine:InvokeLambdaAndRetrieveFile" --input '{"file_to_obfuscate": "s3://gdpr-ingestion-bucket/uk_student_records_1000.parquet", "pii_fields": ["name", "email_address"]}'
### 1. Предварительные требования

- Python 3.9+
- `pip` и `venv`
- AWS CLI

### 2. Настройка локального окружения

1.  **Клонируйте репозиторий:**
    ```bash
    git clone <repository-url>
    cd gdpr-obfuscator
    ```

2.  **Создайте и активируйте виртуальное окружение:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Установите все зависимости для разработки и тестирования:**
    ```bash
    pip install -r requirements-dev.txt
    ```

4.  **Настройте учетные данные AWS:**
    Для локального запуска и тестирования необходимо настроить AWS CLI. Убедитесь, что у вас есть права на чтение и запись в целевой S3 бакет.
    ```bash
    aws configure
    ```

## 💻 Использование

### Запуск из командной строки

Вы можете запустить процесс обфускации локально, передав параметры в виде JSON-строки.

```bash
# Пример для CSV
python -m src.main '{"file_to_obfuscate": "s3://your-bucket/your-file.csv", "pii_fields": ["name", "email"]}'

# Пример для JSON
python -m src.main '{"file_to_obfuscate": "s3://your-bucket/your-file.json", "pii_fields": ["name", "email"]}'

# Пример для Parquet
python -m src.main '{"file_to_obfuscate": "s3://your-bucket/your-file.parquet", "pii_fields": ["name", "email"]}'
```

### Использование как библиотеки

Вы можете импортировать и использовать основную логику в своем Python-коде.

```python
import boto3
from src.s3_utils import obfuscate_data

s3_client = boto3.client("s3")
params = {
    "file_to_obfuscate": "s3://your-bucket/your-file.csv",
    "pii_fields": ["name", "email"]
}

# Получить результат в виде байтов
obfuscated_bytes = obfuscate_data(params, s3_client, return_bytes=True)

# Или выполнить полный цикл с загрузкой в S3 и получить метаданные
result_summary = obfuscate_data(params, s3_client, return_bytes=False)
print(result_summary)
```

## ☁️ Развертывание в AWS Lambda

1.  **Создайте ZIP-архив для развертывания:**
    Этот архив будет содержать ваш код и все production-зависимости.
    ```bash
    # Установите зависимости в директорию package
    pip install -r requirements.txt -t ./package
    
    # Скопируйте ваш исходный код
    cp -r src/* ./package/
    
    # Создайте ZIP-архив
    cd package
    zip -r ../deployment_package.zip .
    cd ..
    ```

2.  **Создайте Lambda-функцию в AWS:**
    - **Имя функции**: `gdpr-obfuscator`
    - **Среда выполнения**: Python 3.9 (или новее)
    - **Архитектура**: x86_64
    - **Обработчик (Handler)**: `lambda_handler.lambda_handler`
    - **Загрузка кода**: Загрузите созданный `deployment_package.zip`.
    - **IAM Роль**: Создайте или используйте роль с правами `s3:GetObject`, `s3:PutObject` и `s3:HeadObject` для бакетов, с которыми будет работать функция.
    - **Тайм-аут**: Установите достаточное время выполнения (например, 1 минута).

3.  **Пример вызова через AWS Step Functions:**
    Вы можете интегрировать Lambda в Step Function. Пример команды для запуска:
    ```bash
    aws stepfunctions start-execution \
      --state-machine-arn "arn:aws:states:..." \
      --input '{"file_to_obfuscate": "s3://your-bucket/your-file.parquet", "pii_fields": ["name", "email_address"]}'
    ```

## 🧪 Тестирование и качество кода

### Запуск тестов

Для запуска полного набора тестов выполните:
```bash
pytest
```

Для просмотра отчета о покрытии кода тестами:
```bash
pytest --cov=src
```

### Статический анализ безопасности

Проект использует `bandit` для поиска распространенных уязвимостей в коде.
```bash
bandit -r src/
```
