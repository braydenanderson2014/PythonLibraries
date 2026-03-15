"""
Tag System for Financial Tracker
Provides flexible tagging for transactions beyond single categories
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from assets.Logger import Logger
logger = Logger()


class Tag:
    """Represents a tag that can be applied to transactions"""
    
    def __init__(self, name, color='#808080', description='', created_date=None, tag_id=None):
        """
        Initialize a tag.
        
        Args:
            name: Tag name (e.g., 'tax-deductible', 'work-related')
            color: Hex color code for UI display
            description: Optional description of tag purpose
            created_date: When tag was created
            tag_id: Unique identifier
        """
        self.tag_id = tag_id or self._generate_tag_id()
        self.name = name.strip().lower()  # Normalize to lowercase
        self.color = color
        self.description = description
        self.created_date = created_date or datetime.now().isoformat()
        self.usage_count = 0  # Tracked by TagManager
    
    def _generate_tag_id(self):
        """Generate unique tag ID"""
        import uuid
        return f"tag_{uuid.uuid4().hex[:8]}"
    
    def to_dict(self):
        """Convert tag to dictionary for JSON serialization"""
        return {
            'tag_id': self.tag_id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'created_date': self.created_date
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create tag from dictionary"""
        return cls(
            name=data['name'],
            color=data.get('color', '#808080'),
            description=data.get('description', ''),
            created_date=data.get('created_date'),
            tag_id=data.get('tag_id')
        )
    
    def __str__(self):
        return self.name
    
    def __eq__(self, other):
        if isinstance(other, Tag):
            return self.name == other.name
        return False
    
    def __hash__(self):
        return hash(self.name)


class TagManager:
    """Manages tags and tag-related operations"""
    
    # Predefined common tags with colors
    DEFAULT_TAGS = [
        {'name': 'tax-deductible', 'color': '#4CAF50', 'description': 'Tax deductible expenses'},
        {'name': 'reimbursable', 'color': '#2196F3', 'description': 'To be reimbursed by employer'},
        {'name': 'work-related', 'color': '#FF9800', 'description': 'Work and business expenses'},
        {'name': 'personal', 'color': '#9C27B0', 'description': 'Personal expenses'},
        {'name': 'urgent', 'color': '#F44336', 'description': 'Urgent or important'},
        {'name': 'recurring', 'color': '#795548', 'description': 'Recurring expense'},
        {'name': 'one-time', 'color': '#607D8B', 'description': 'One-time purchase'},
        {'name': 'gift', 'color': '#E91E63', 'description': 'Gift or present'},
    ]
    
    def __init__(self, tags_file='resources/tags.json'):
        """
        Initialize Tag Manager.
        
        Args:
            tags_file: Path to tags JSON file
        """
        logger.debug("TagManager", f"Initializing TagManager with tags_file={tags_file}")
        self.tags_file = tags_file
        self.tags = {}  # tag_id -> Tag
        self.load()
        logger.info("TagManager", f"TagManager initialized with {len(self.tags)} tags")
    
    def load(self):
        """Load tags from JSON file"""
        logger.debug("TagManager", f"Loading tags from {self.tags_file}")
        if os.path.exists(self.tags_file):
            try:
                with open(self.tags_file, 'r') as f:
                    data = json.load(f)
                    self.tags = {
                        tag_data['tag_id']: Tag.from_dict(tag_data)
                        for tag_data in data
                    }
                logger.info("TagManager", f"Loaded {len(self.tags)} tags from file")
            except Exception as e:
                logger.error("TagManager", f"Failed to load tags: {e}")
                self.tags = {}
        else:
            # Create file with default tags
            logger.debug("TagManager", "Tags file not found, creating with default tags")
            self.tags = {}
            self.initialize_default_tags()
            self.save()
    
    def save(self):
        """Save tags to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.tags_file), exist_ok=True)
            
            with open(self.tags_file, 'w') as f:
                data = [tag.to_dict() for tag in self.tags.values()]
                json.dump(data, f, indent=2)
            logger.debug("TagManager", f"Saved {len(self.tags)} tags to file")
        except Exception as e:
            logger.error("TagManager", f"Failed to save tags: {e}")
    
    def initialize_default_tags(self):
        """Add default tags to the system"""
        for tag_data in self.DEFAULT_TAGS:
            tag = Tag(
                name=tag_data['name'],
                color=tag_data['color'],
                description=tag_data['description']
            )
            self.tags[tag.tag_id] = tag
    
    def add_tag(self, name, color='#808080', description=''):
        """
        Add a new tag.
        
        Args:
            name: Tag name
            color: Hex color code
            description: Optional description
        
        Returns:
            Tag: Created tag or None if name exists
        """
        logger.debug("TagManager", f"Adding tag: {name}")
        normalized_name = name.strip().lower()
        
        # Check if tag with this name already exists
        if self.get_tag_by_name(normalized_name):
            logger.warning("TagManager", f"Tag already exists: {normalized_name}")
            return None
        
        tag = Tag(name=normalized_name, color=color, description=description)
        self.tags[tag.tag_id] = tag
        self.save()
        logger.info("TagManager", f"Tag created: {normalized_name}")
        return tag
    
    def update_tag(self, tag_id, name=None, color=None, description=None):
        """
        Update an existing tag.
        
        Args:
            tag_id: Tag ID to update
            name: New name (optional)
            color: New color (optional)
            description: New description (optional)
        
        Returns:
            bool: Success status
        """
        logger.debug("TagManager", f"Updating tag: {tag_id}")
        if tag_id not in self.tags:
            logger.warning("TagManager", f"Tag not found: {tag_id}")
            return False
        
        tag = self.tags[tag_id]
        
        if name is not None:
            normalized_name = name.strip().lower()
            # Check if new name conflicts with another tag
            existing = self.get_tag_by_name(normalized_name)
            if existing and existing.tag_id != tag_id:
                logger.warning("TagManager", f"Tag name conflict: {normalized_name}")
                return False
            tag.name = normalized_name
        
        if color is not None:
            tag.color = color
        
        if description is not None:
            tag.description = description
        
        self.save()
        logger.info("TagManager", f"Tag updated: {tag_id}")
        return True
    
    def delete_tag(self, tag_id):
        """
        Delete a tag.
        
        Args:
            tag_id: Tag ID to delete
        
        Returns:
            bool: Success status
        """
        logger.debug("TagManager", f"Deleting tag: {tag_id}")
        if tag_id in self.tags:
            tag_name = self.tags[tag_id].name
            del self.tags[tag_id]
            self.save()
            logger.info("TagManager", f"Tag deleted: {tag_name}")
            return True
        logger.warning("TagManager", f"Tag not found for deletion: {tag_id}")
        return False
    
    def get_tag(self, tag_id):
        """Get tag by ID"""
        return self.tags.get(tag_id)
    
    def get_tag_by_name(self, name):
        """
        Get tag by name (case-insensitive).
        
        Args:
            name: Tag name to search for
        
        Returns:
            Tag or None
        """
        normalized_name = name.strip().lower()
        for tag in self.tags.values():
            if tag.name == normalized_name:
                return tag
        return None
    
    def list_tags(self, sort_by='name'):
        """
        List all tags.
        
        Args:
            sort_by: Sort key ('name', 'created_date', 'usage_count')
        
        Returns:
            List of tags
        """
        logger.debug("TagManager", f"Listing tags sorted by {sort_by}")
        tags_list = list(self.tags.values())
        
        if sort_by == 'name':
            tags_list.sort(key=lambda t: t.name)
        elif sort_by == 'created_date':
            tags_list.sort(key=lambda t: t.created_date, reverse=True)
        elif sort_by == 'usage_count':
            tags_list.sort(key=lambda t: t.usage_count, reverse=True)
        
        return tags_list
    
    def search_tags(self, query):
        """
        Search tags by name or description.
        
        Args:
            query: Search query
        
        Returns:
            List of matching tags
        """
        query_lower = query.lower()
        matches = []
        
        for tag in self.tags.values():
            if (query_lower in tag.name.lower() or 
                query_lower in tag.description.lower()):
                matches.append(tag)
        
        return matches
    
    def get_or_create_tag(self, name, color='#808080'):
        """
        Get existing tag by name or create new one.
        
        Args:
            name: Tag name
            color: Color for new tag
        
        Returns:
            Tag instance
        """
        tag = self.get_tag_by_name(name)
        if tag:
            return tag
        
        return self.add_tag(name, color)
    
    def normalize_tag_names(self, tag_names):
        """
        Normalize list of tag names to tag objects.
        
        Args:
            tag_names: List of tag name strings
        
        Returns:
            List of Tag objects
        """
        tags = []
        for name in tag_names:
            tag = self.get_tag_by_name(name)
            if tag:
                tags.append(tag)
        return tags
    
    def update_usage_counts(self, transactions):
        """
        Update usage counts for all tags based on transactions.
        
        Args:
            transactions: List of transaction dictionaries with 'tags' field
        """
        # Reset counts
        for tag in self.tags.values():
            tag.usage_count = 0
        
        # Count usage
        for transaction in transactions:
            if 'tags' in transaction and transaction['tags']:
                for tag_name in transaction['tags']:
                    tag = self.get_tag_by_name(tag_name)
                    if tag:
                        tag.usage_count += 1
    
    def get_tag_statistics(self, transactions):
        """
        Get statistics about tag usage.
        
        Args:
            transactions: List of transaction dictionaries
        
        Returns:
            dict: Statistics including usage counts, spending per tag, etc.
        """
        self.update_usage_counts(transactions)
        
        # Calculate spending per tag
        tag_spending = {}
        tag_income = {}
        tag_counts = {}
        
        for transaction in transactions:
            if 'tags' not in transaction or not transaction['tags']:
                continue
            
            amount = transaction['amount']
            tx_type = transaction['type']
            
            for tag_name in transaction['tags']:
                if tag_name not in tag_counts:
                    tag_counts[tag_name] = 0
                    tag_spending[tag_name] = 0.0
                    tag_income[tag_name] = 0.0
                
                tag_counts[tag_name] += 1
                
                if tx_type == 'out':
                    tag_spending[tag_name] += amount
                else:
                    tag_income[tag_name] += amount
        
        # Compile statistics
        stats = {
            'total_tags': len(self.tags),
            'used_tags': len(tag_counts),
            'unused_tags': len(self.tags) - len(tag_counts),
            'most_used': [],
            'highest_spending': [],
            'tag_details': []
        }
        
        # Most used tags (top 10)
        sorted_by_usage = sorted(
            tag_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        stats['most_used'] = [
            {'name': name, 'count': count}
            for name, count in sorted_by_usage
        ]
        
        # Highest spending tags (top 10)
        sorted_by_spending = sorted(
            tag_spending.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        stats['highest_spending'] = [
            {'name': name, 'amount': amount}
            for name, amount in sorted_by_spending
        ]
        
        # Detailed stats for each tag
        for tag in self.list_tags(sort_by='usage_count'):
            tag_name = tag.name
            stats['tag_details'].append({
                'tag': tag,
                'usage_count': tag_counts.get(tag_name, 0),
                'spending': tag_spending.get(tag_name, 0.0),
                'income': tag_income.get(tag_name, 0.0),
                'net': tag_income.get(tag_name, 0.0) - tag_spending.get(tag_name, 0.0)
            })
        
        return stats
    
    def export_tags(self, file_path):
        """Export tags to CSV file"""
        import csv
        
        try:
            from datetime import datetime
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])
                writer.writerow(['Tag ID', 'Name', 'Color', 'Description', 'Created Date'])
                
                for tag in self.list_tags():
                    writer.writerow([
                        tag.tag_id,
                        tag.name,
                        tag.color,
                        tag.description,
                        tag.created_date
                    ])
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to export tags: {e}")
            return False
    
    def import_tags(self, file_path):
        """Import tags from CSV file"""
        import csv
        
        imported_count = 0
        
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Skip if tag already exists
                    if self.get_tag_by_name(row['Name']):
                        continue
                    
                    self.add_tag(
                        name=row['Name'],
                        color=row.get('Color', '#808080'),
                        description=row.get('Description', '')
                    )
                    imported_count += 1
            
            return imported_count
        except Exception as e:
            print(f"[ERROR] Failed to import tags: {e}")
            return 0
