from search import search_prompt

EXIT_COMMANDS = {"sair", "exit", "quit"}


def main():
    chain = search_prompt()

    if not chain:
        print("Não foi possível iniciar o chat. Verifique os erros de inicialização.")
        return

    print("Faça sua pergunta (digite 'sair' para encerrar):\n")

    while True:
        try:
            question = input("PERGUNTA: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando o chat.")
            break

        if not question:
            continue
        if question.lower() in EXIT_COMMANDS:
            print("Encerrando o chat.")
            break

        try:
            answer = chain.invoke(question)
        except KeyboardInterrupt:
            print("\nPergunta cancelada.")
            continue
        except Exception as exc:
            print(f"Erro ao processar a pergunta: {exc}")
            continue

        print(f"RESPOSTA: {answer.strip()}\n")
        print("---\n")


if __name__ == "__main__":
    main()
