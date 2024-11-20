from django.views import View
from django.shortcuts import render


class HomeView(View):
    """
    1. When you use @staticmethod on a method inside a class:
       - The method does not receive the implicit self or cls parameter.
       - It can be called directly from the class without creating an instance.
       - It behaves like a regular function defined outside of a class but is namespaced
       inside the class.

    2. When you apply @classmethod to a method:
       - Python Passes the Class: Python passes the class (not an instance)
       as the first argument to the method. By convention, this argument is
       named cls.
       - Access Class Attributes: You can access class-level attributes or
       modify them through cls.
       - Return an Instance: Since cls is the class itself, you can return
       a new instance of the class by calling cls(...) within the method.
       This is particularly useful for creating alternative constructors.
    """

    template_name = "home.html"

    def get(self, request, *args, **kwargs):
        # Use `data_source` if it exists; otherwise, load and process default data
        data = (
            self.data_source
            if hasattr(self, "data_source")
            else self.process_data(self.load_data())
        )
        context = {"processed_data": data}
        return render(request, self.template_name, context)

    @classmethod
    def with_custom_data(cls, custom_data_source=None):
        # Define a custom class-based view that sets `data_source`
        class CustomHomeView(cls):
            cls_data = cls.process_data(cls.load_data(cls))
            data_source = custom_data_source or cls_data

        return CustomHomeView.as_view()

    @staticmethod
    def process_data(data):
        """
        Static method to process data without depending on instance or class state
        """
        return [item.upper() for item in data]

    def load_data(self):
        """
        Assume we are loading some data; in reality, this could be from self.data_source
        """
        return []


home_custom = HomeView.with_custom_data()
home = HomeView.as_view()
