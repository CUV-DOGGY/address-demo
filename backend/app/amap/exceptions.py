class AmapError(RuntimeError):
    """高德服务调用异常基类。"""


class AmapAddressFetchError(AmapError):
    """高德服务未返回可用的地址数据。"""


class AmapAddressNotFoundError(AmapError):
    """高德服务未找到对应的地址。"""


class AmapConfigurationError(AmapError):
    """高德服务鉴权或权限配置错误。"""


class AmapServiceUnavailableError(AmapError):
    """高德服务当前不可用。"""


class AmapServiceTimeoutError(AmapError):
    """调用高德服务超时。"""
