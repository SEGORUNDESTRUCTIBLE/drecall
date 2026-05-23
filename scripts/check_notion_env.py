import os
print('NOTION_API_KEY', 'present' if os.environ.get('NOTION_API_KEY') else 'missing')
print('NOTION_DATASOURCE_ID', 'present' if os.environ.get('NOTION_DATASOURCE_ID') else 'missing')
print('NOTION_DATABASE_ID', 'present' if os.environ.get('NOTION_DATABASE_ID') else 'missing')
print('ENABLE_NOTION', os.environ.get('ENABLE_NOTION'))
