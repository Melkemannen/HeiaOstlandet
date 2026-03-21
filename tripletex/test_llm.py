from llm import classify_and_extract

prompts = [
    "Opprett en ansatt med navn Ola Nordmann, ola@example.org. Han skal være kontoadministrator.",
    "Create a customer called Acme AS with email post@acme.no",
    "Lag en faktura til kunden Acme AS med forfallsdato 2026-04-21",
    "Create a new product called Hammer with price 99 NOK",
]

for prompt in prompts:
    print(f"\nPrompt: {prompt}")
    task_type, fields = classify_and_extract(prompt)
    print(f"Task type: {task_type}")
    print(f"Fields:    {fields}")
