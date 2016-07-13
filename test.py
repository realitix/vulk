import pyVulkan

applicationInfo = pyVulkan.VkApplicationInfo(
    sType=pyVulkan.VK_STRUCTURE_TYPE_APPLICATION_INFO,
    pNext=None,
    pApplicationName="Vulk",
    pEngineName="Vulk-Graphic",
    engineVersion=1,
    apiVersion=pyVulkan.VK_API_VERSION
)

instanceInfo = pyVulkan.VkInstanceCreateInfo(
    sType=pyVulkan.VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
    pNext=None,
    flags=0,
    pApplicationInfo=applicationInfo,
    enabledLayerCount=0,
    ppEnabledLayerNames=None,
    enabledExtensionCount=0,
    ppEnabledExtensionNames=None
)

instance = pyVulkan.vkCreateInstance(instanceInfo, None)

pyVulkan.vkDestroyInstance(instance, None)
