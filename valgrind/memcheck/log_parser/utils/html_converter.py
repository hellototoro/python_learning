import os
import json
from jinja2 import Environment, FileSystemLoader

def data_convert(row_data):
    try:
        summary = row_data.get('memory_leak_summary')[0]
    except (TypeError, IndexError):
        summary = "ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)"
    data = [
    {"类型": "definitely", "数量": len(row_data.get('memory_leak_definitely')), "位置": row_data.get('memory_leak_definitely')},
    {"类型": "indirectly", "数量": len(row_data.get('memory_leak_indirectly')), "位置": row_data.get('memory_leak_indirectly')},
    {"类型": "possibly", "数量": len(row_data.get('memory_leak_possibly')), "位置": row_data.get('memory_leak_possibly')},
    {"类型": "still reachable", "数量": len(row_data.get('memory_leak_still_reachable')), "位置": row_data.get('memory_leak_still_reachable')} ]
    return data, summary

def dump_html_report(app_name, row_data, html_path):
    data, summary = data_convert(row_data)
    path = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(path+'/../data'))
    template = env.get_template('template.html')

    with open(html_path, 'w+', encoding='utf-8') as f:
        out = template.render(app_name=app_name,
                            summary=summary,
                            leak_types=data)
        f.write(out)
        f.close()


def dump_json_report(row_data, json_path):
    data, summary = data_convert(row_data)
    with open(json_path, 'w+', encoding='utf-8') as f:
        json.dump({'summary': summary, 'leak_types': data}, f, ensure_ascii=False, indent=4)
        f.close()
