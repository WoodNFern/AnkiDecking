import re

class TemplateProcessor():

    @staticmethod
    def process_templates(wiki_text: str):
        processed_text = wiki_text
        p = re.compile(r"{{([^\|]*?)\|(.*?)}}")
        t_coordinates = TemplateProcessor.detect_template_coordinates(processed_text)

        while t_coordinates:
            # Extract template information
            start_index, end_index = t_coordinates.pop(0)
            m = p.search(processed_text[start_index:end_index])
            t_type, t_args = (m.group(1), m.group(2)) if m else ('', '')

            # Substitute template with processed text
            processed_template = TemplateProcessor.process_specific_template(t_type, t_args)
            processed_text = processed_text[:start_index] + processed_template + processed_text[end_index:]
            t_coordinates = TemplateProcessor.detect_template_coordinates(processed_text)

        return processed_text

    @staticmethod
    def detect_template_coordinates(wiki_text: str):
        t_coordinates = []
        stack = []

        i = 0
        while i < len(wiki_text) - 1:
            if wiki_text[i:i+2] == '{{':
                stack.append(i)
            elif wiki_text[i:i+2] == '}}':
                start_index = stack.pop()
                end_index = i + 2
                t_coordinates.append((start_index, end_index))
                i += 1  # next character is already processed -> skip
            else:
                pass
            i += 1

        return t_coordinates

    @staticmethod
    def process_specific_template(t_type: str, t_args: str):
        if t_type in ['m', 'mention']:
            return TemplateProcessor.unchanged_text_with_opt_remark(t_args)
        elif t_type in ['l', 'link']:
            return TemplateProcessor.get_second_arg(t_args)
        elif t_type in ['lb', 'label']:
            return TemplateProcessor.omit_template()
        elif t_type in ['gloss', 'qualifier', 'qual', 'q']:
            return TemplateProcessor.parenthesized_arg(t_args)
        elif t_type in ['taxlink', 'w', 'n-g', 'non-gloss definition', 'vern']:
            return TemplateProcessor.get_first_arg(t_args)
        elif any(particle in t_type for particle in ['for', 'form']) :
            return TemplateProcessor.leave_marked(t_type, t_args)
        elif t_type in ['cln']:
            return TemplateProcessor.omit_template()
        else:
            return TemplateProcessor.omit_template()

    @staticmethod
    def unchanged_text_with_opt_remark(t_args: str):
        """
        Produces the unprocessed mention from the first argument and appends an
        optional further remark in quotes and parentheses from the second
        argument, if present.
        """
        splits = re.split(r'\|+', t_args)

        mention = splits[1]
        if len(splits) == 3:
            mention += ' ("' + splits[2] + '")'

        return mention

    @staticmethod
    def get_first_arg(t_args: str):
        splits = re.split(r'\|+', t_args)

        return splits[0]

    @staticmethod
    def get_second_arg(t_args: str):
        splits = re.split(r'\|+', t_args)

        return splits[1]

    @staticmethod
    def parenthesized_arg(t_args: str):
        """
        Returns the provided arguments unchanged, put between parantheses.
        """
        return '(%s)' % t_args

    @staticmethod
    def leave_marked(t_type: str, t_args: str):
        """
        Leave template marked to be detected later on such that the whole
        containing translation can be deleted instead of merely removing the
        template.
        """
        return '$$' + t_type + '|' + t_args + '$$'

    @staticmethod
    def omit_template():
        """
        Omit unknown templates with the assumption that new templates are not
        going to introduce fundamental new information.
        """
        return ''