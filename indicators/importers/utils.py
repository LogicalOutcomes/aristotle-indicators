from aristotle_mdr import models
from aristotle_mdr.contrib.identifiers import models as MDR_ID


class BaseImporter(object):

    def process_authorities(self):
        self.authority, created = models.RegistrationAuthority.objects.get_or_create(
            name=self.DEFAULT_AUTHORITY_NAME
        )
        self.authority_org = models.Organization.objects.get(
            pk=self.authority.pk
        )
        self.authority_namespace, c = MDR_ID.Namespace.objects.get_or_create(
            naming_authority=self.authority_org,
            shorthand_prefix=self.DEFAULT_AUTHORITY_PREFIX
        )

    # Importer Helpers
    def define_data_type(self, name):
        dt, c = models.DataType.objects.get_or_create(name=name)
        if c:
            self.register(dt)
        return dt

    def register(self, thing):
        """Aristotle MDR regiter
        """
        models.Status.objects.get_or_create(
            concept=thing,
            registrationAuthority=self.authority,
            registrationDate=self.DEFAULT_REGISTRATION_DATE,
            state=models.STATES.recorded
        )


def get_col(row, col):
    for cell in row:
        if cell.value is not None:
            if cell.coordinate.startswith(col):
                return cell


def lb_2_p(txt, sep="\n\n"):
    if sep in txt:
        return "<p>"+"</p><p>".join([l for l in txt.split(sep) if l != ""]) + "</p>"
    else:
        return txt
