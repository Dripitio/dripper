from mailchimp import Mailchimp


class MailchimpWrapper:
    def __init__(self, api_key):
        self.mc = Mailchimp(api_key)

    def get_lists(self):
        """
        returns list of lists
        each list is described by a dict of name and list_id
        """
        return [{"name": lst["name"], "list_id": lst["id"]}
                for lst in self.mc.lists.list()["data"]]

    def get_templates(self):
        """
        returns list of templates
        each template is described by a dict of name and template_id
        """
        return [{"name": tmplt["name"], "template_id": tmplt["id"]}
                for tmplt in self.mc.templates.list(filters={"include_drag_and_drop": True})["user"]]

    def get_folders(self):
        """
        returns list of folders
        each folder is described by a dict of name and folder_id
        """
        return [{"name": fldr["name"], "folder_id": fldr["folder_id"]}
                for fldr in self.mc.folders.list("campaign")]

    def get_template_source(self, template_id):
        """
        given template_id get source of template
        """
        return self.mc.templates.info(template_id)["source"]

    def create_folder(self, name):
        """
        create folder with name `name` and return folder_id
        """
        return self.mc.folders.add(name, "campaign")["folder_id"]