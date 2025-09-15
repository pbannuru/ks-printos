# from ast import List
from enum import Enum as EnumEnum
from typing import List


class PersonaEnum(EnumEnum):
    Operator = "operator"
    Engineer = "engineer"

class kzPersonaEnum(EnumEnum):
    PressOperatorLevel1 = "Press Operator Level 1"
    Channel = "channel"              
    HPCE  = "HP CE"                
    PressOperatorLevel2 = "Press Operator Level 2"  
    ChannelLevel2 = "Channel Level 2"      
    PressOperatorLevel3 = "Press Operator Level 3"                     
    KZAdmin = "KZ Admin"             
    PSPAdmin = "PSP Admin"
    
class DomainEnum(EnumEnum):
    Indigo = "indigo"
    PWP = "pwp"
    Scitex= "scitex"
    ThreeD= "ThreeD"


class SourceEnum(EnumEnum):
    All = "all"
    KZ = "kz"
    Kaas = "kaas"
    Docebo = "docebo"


class LanguageEnum(EnumEnum):
    English = "en"
    Chinese = "zh"
    French = "fr"
    German = "de"
    Japanese = "ja"
    Korean = "ko"
    Portuguese = "pt"
    Russian = "ru"
    Spanish = "es"
    Italian = "it"
    PortugueseBr = "pt-BR"
    Hebrew = "he"
    SpanishLatam = "es-419"
    Hungarian = "hu"
    Dutch = "nl"
    SimplifiedChinese = "zh-CN"
    Others = "xx"  # Handles other unspecified languages

from enum import Enum
from pydantic import BaseModel, Field

class SafetyAssessment(Enum):
    SAFE = "safe"
    UNSAFE = "unsafe"
    ERROR = "error"

class LlamaGuardOutput(BaseModel):
    safety_assessment: SafetyAssessment = Field(
        description="The safety assessment of the content."
    )
    unsafe_categories: List[str] = Field(
        description="If content is unsafe, the list of unsafe categories.", default=[]
    )
