"""Draft intent only. Product adapters are unsupported; never generate media/drafts."""
from pathlib import Path

PRODUCTS={'jianying':('jianying',),'capcut':('capcut',),'both':('jianying','capcut')}

def from_export_choices(choices):
    if 'draft_package' in choices and 'jianying_draft' in choices:
        raise ValueError('Use one draft_package entry; conflicting legacy entry')
    if 'draft_package' in choices:return choices['draft_package']
    old=choices.get('jianying_draft')
    if old is None:return None
    if not isinstance(old,dict) or set(old)-{'requested','platform','version','materials'}:raise ValueError('Invalid legacy draft choice')
    return {'requested':old.get('requested'),'selection':'jianying','materials':old.get('materials'),
            'targets':{'jianying':{'platform':old.get('platform'),'version':old.get('version')}}}

def resolve(choice, output_dir):
    if choice is None:choice={}
    if not isinstance(choice,dict) or set(choice)-{'requested','selection','materials','targets'}:raise ValueError('Invalid draft_package choices')
    requested=choice.get('requested');selection=choice.get('selection');materials=choice.get('materials')
    if requested is not None and type(requested) is not bool:raise ValueError('requested must be true, false or null')
    if selection is not None and (not isinstance(selection,str) or selection not in PRODUCTS):raise ValueError('Choose jianying, capcut or both')
    if materials not in (None,'copy','reference'):raise ValueError('Choose copied materials or original-path references')
    supplied=choice.get('targets',{})
    if not isinstance(supplied,dict) or set(supplied)-set(PRODUCTS.get(selection,())):raise ValueError('Target details must match selected products')
    targets={}
    for product in PRODUCTS.get(selection,()):
        details=supplied.get(product,{})
        if not isinstance(details,dict) or set(details)-{'platform','version','build'}:raise ValueError('Invalid target details; capability is not user input')
        platform,version,build=(details.get(k) for k in ('platform','version','build'))
        if platform not in (None,'macOS','Windows'):raise ValueError('Confirm desktop platform macOS or Windows')
        for v in (version,build):
            if v is not None and (not isinstance(v,str) or not v.strip()):raise ValueError('Confirm exact target version/build')
        targets[product]={'platform':platform,'version':version,'build':build,'support_status':'unsupported',
          'validation_status':'not_tested','exporter_available':False,'generation_allowed':False,'artifact':None,
          'missing_details':[k for k,v in [('platform',platform),('version',version),('materials',materials)] if v is None],
          'planned_output_dir':str(Path(output_dir)/(product+'-draft')) if requested is True else None}
    status='pending_confirmation' if requested is None else ('not_requested' if requested is False else ('pending_target' if selection is None else 'unsupported'))
    return {'requested':requested,'selection':selection,'materials':materials,'status':status,'targets':targets,
      'exporter_available':False,'generation_allowed':False,'artifact':None}

def require_video_render(state):
    if state['requested'] is None:raise ValueError('草稿包選項待確認：請先回答是／否；不自動生成')
    if state['requested'] is True:
        if state['selection'] is None:raise ValueError('草稿目標待確認：剪映／CapCut／兩者都要')
        raise ValueError('所選草稿 exporter 尚未支援；保留各產品需求，不以成片渲染代替')
