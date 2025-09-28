from rest_framework import renderers
import json


class LibraryJSONRenderer(renderers.JSONRenderer):
    """
    Custom JSON renderer that wraps the response in a standardized format.
    
    Example:
    {
        "success": true,
        "data": { ... },
        "message": "Operation completed successfully"
    }
    """
    charset = 'utf-8'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, returning a bytestring.
        """
        response_dict = {
            'success': True,
            'data': data,
            'message': ''
        }
        
        # Check for errors in the response
        response = renderer_context.get('response') if renderer_context else None
        if response and response.status_code >= 400:
            response_dict['success'] = False
            
            # Handle validation errors
            if 'detail' in data:
                response_dict['message'] = data['detail']
            elif 'non_field_errors' in data:
                response_dict['message'] = data['non_field_errors'][0]
            else:
                response_dict['message'] = 'An error occurred'
                response_dict['errors'] = data
        
        return json.dumps(response_dict).encode(self.charset)


class LibraryCSVRenderer(renderers.BaseRenderer):
    """
    Custom CSV renderer for exporting data in CSV format.
    """
    media_type = 'text/csv'
    format = 'csv'
    
    def render(self, data, media_type=None, renderer_context=None):
        """
        Render `data` into CSV, returning a bytestring.
        """
        # This is a simplified example. In a real implementation, you would
        # convert the data to CSV format using the csv module.
        import csv
        from io import StringIO
        
        if not data:
            return b''
            
        # Handle paginated responses
        if 'results' in data:
            data = data['results']
        
        # Convert data to CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header row if this is the first row
        if data and isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                writer.writerow(data[0].keys())
                
                # Write data rows
                for row in data:
                    writer.writerow(row.values())
        
        return output.getvalue().encode(self.charset)


class LibraryAPIRenderer(renderers.JSONRenderer):
    """
    A more sophisticated API response renderer that handles pagination,
    metadata, and error responses consistently.
    """
    charset = 'utf-8'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON with consistent response format.
        """
        response_dict = {
            'version': '1.0',
            'success': True,
            'data': None,
            'meta': {},
            'errors': []
        }
        
        response = renderer_context.get('response') if renderer_context else None
        
        # Handle error responses
        if response and response.status_code >= 400:
            response_dict['success'] = False
            
            if isinstance(data, dict):
                if 'detail' in data:
                    response_dict['errors'].append({
                        'code': response.status_code,
                        'message': data['detail']
                    })
                else:
                    # Handle validation errors
                    for field, errors in data.items():
                        if isinstance(errors, list):
                            for error in errors:
                                response_dict['errors'].append({
                                    'code': 'validation_error',
                                    'field': field,
                                    'message': error
                                })
                        else:
                            response_dict['errors'].append({
                                'code': 'validation_error',
                                'field': field,
                                'message': str(errors)
                            })
            
            return json.dumps(response_dict).encode(self.charset)
        
        # Handle successful responses
        if isinstance(data, dict) and 'results' in data:
            # This is a paginated response
            response_dict['data'] = data.pop('results')
            response_dict['meta'] = {
                'count': data.get('count', 0),
                'next': data.get('next'),
                'previous': data.get('previous'),
                'page_size': data.get('page_size', 10)
            }
        else:
            response_dict['data'] = data
        
        # Add any additional context from the view
        view = renderer_context.get('view') if renderer_context else None
        if view and hasattr(view, 'get_renderer_context'):
            renderer_context_data = view.get_renderer_context()
            if 'message' in renderer_context_data:
                response_dict['message'] = renderer_context_data['message']
        
        return json.dumps(response_dict).encode(self.charset)
