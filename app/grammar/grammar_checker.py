
import language_tool_python


class GrammarChecker:

    def __init__(self, language="en-US"):
        self.tool = language_tool_python.LanguageTool(language)

    def check_grammar(self, text):

        if not text or not text.strip():
            return []

        matches = self.tool.check(text)

        errors = []

        for match in matches:

            wrong_text = text[
                match.offset:
                match.offset + match.error_length
            ]

            errors.append({
                "message": match.message,
                "wrong_text": wrong_text,
                "suggestions": match.replacements,
                "offset": match.offset,
                "error_length": match.error_length
            })

        return errors

    def correct_text(self, text):

        if not text or not text.strip():
            return ""

        return self.tool.correct(text)

    def close(self):
        self.tool.close()
