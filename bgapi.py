# -*- coding: utf-8 -*-
import requests

__author__ = 'Andrey Smirnov'
__email__ = 'mail@ansmirnov.ru'

from lxml.etree import Element, fromstring
from zeep import Client


class SOAP_BGServer:
    """
    Описывает сервер BGBilling
    """
    def __init__(self, url):
        self.url = url


class SOAP_BGUser:
    """
    Описывает пользователя BGBilling
    """
    def __init__(self, user, pswd, xmlns="http://ws.base.kernel.bgbilling.bitel.ru"):
        self.user = user
        self.pswd = pswd
        self.xmlns = xmlns

    def get_auth_header(self):
        """
        Возвращает XML-заголовок для авторизации пользователя
        """
        return Element('auth', {
            'xmlns': self.xmlns,
            'user': self.user,
            'pswd': self.pswd
        })

    def as_dict(self):
        return {
            'user': self.user,
            'pswd': self.pswd,
        }


class SOAP_BGService:
    """
    Описывает WEB-сервис билинга
    """
    def __init__(self, bgserver, package, module):
        self.bgserver = bgserver
        self.package = package
        self.module = module
        self.service = Client(self.wsdl()).service

    def wsdl(self):
        """
        Возвращает URL WSDL-схемы сервера
        """
        return "{bgserver_url:s}/{package:s}/{module:s}?wsdl".format(bgserver_url=self.bgserver.url,
                                                                     package=self.package, module=self.module)

    def __getattr__(self, item):
        """
        Все прочие вызовы проксирует на SOAP-сервис.

        Первым параметром при вызове сервиса должен быть объект BGUser, содержащий параметры
        """
        def f(*args, **kwargs):
            return self.service.__getattr__(item).__call__(_soapheaders=[args[0].get_auth_header()], *args[1:], **kwargs)

        return f


class AuthError(BaseException):
    pass


class OldService:
    """
    Описывает старый HTTP-экшен биллинга

    Пример вызова для получения данных контракта:

    ```
    service = new OldService(bgserver, 'contract')
    service.ContractInfo(bguser, cid=17272)
    ```

    Объект BGUser должен передаваться первым аргументом.

    Для передачи параметров метода необходимо использовать непозиционные (именованные) аргументы.
    """
    def __init__(self, bgserver, module):
        self.bgserver = bgserver
        self.module = module

    def __repr__(self):
        return "OldService('{bgserver:s}', '{module:s}')".format(bgserver=self.bgserver, module=self.module)

    def __getattr__(self, action):
        def f(*args, **kwargs):
            if len(args) != 1 or not isinstance(args[0], SOAP_BGUser):
                raise AuthError('First argument must be a BGUser instance')
            kwargs.update(args[0].as_dict())
            kwargs['module'] = self.module
            kwargs['action'] = action
            response = requests.get(self.bgserver.url, params=kwargs)
            return fromstring(response.content)

        return f