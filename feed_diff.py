#!/usr/bin/env python
#
# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

__author__ = 'bslatkin@gmail.com (Brett Slatkin)'

"""Atom/RSS feed parser that quickly extracts entry/item elements."""

import cStringIO
import logging
import xml.sax
import xml.sax.handler
import xml.sax.saxutils
#SMOB: Start adding another xml library
import xml.dom.minidom
import re
# Set to true to see stack level messages and other debugging information.
DEBUG = False


class Error(Exception):
  """Exception for errors in this module."""


class TrivialEntityResolver(xml.sax.handler.EntityResolver):
  """Pass-through entity resolver."""

  def resolveEntity(self, publicId, systemId):
    return cStringIO.StringIO()


class FeedContentHandler(xml.sax.handler.ContentHandler):
  """Sax content handler for quickly parsing Atom and RSS feeds."""

  def __init__(self, parser):
    """Initializer.

    Args:
      parser: Instance of the xml.sax parser being used with this handler.
    """
    self.enclosing_tag = ""
    self.parser = parser
    self.header_footer = ""
    self.entries_map = {}
    self.entries_restrictions_map = {}
    # Internal state
    self.stack_level = 0
    self.output_stack = []
    self.current_level = None
    self.last_id = ''
    self.last_link = ''
    self.last_title = ''
    self.last_description = ''

  # Helper methods
  def emit(self, data):
    if type(data) is list:
      self.current_level.extend(data)
    else:
      self.current_level.append(data)

  def push(self):
    self.current_level = []
    self.output_stack.append(self.current_level)

  def pop(self):
    old_level = self.output_stack.pop()
    if len(self.output_stack) > 0:
      self.current_level = self.output_stack[-1]
    else:
      self.current_level = None
    return old_level

  # SAX methods
  def startElement(self, name, attrs):
    self.stack_level += 1
    event = (self.stack_level, name)
    if DEBUG: logging.debug('Start stack level %r', event)
    if self.stack_level == 1:
      # Save the outermost tag for later.
      self.enclosing_tag = name.lower()

    self.push()
    self.emit(['<', name])
    for key, value in attrs.items():
      self.emit([' ', key, '=', xml.sax.saxutils.quoteattr(value)])
    # Do not emit a '>' here because this tag may need to be immediately
    # closed with a '/> ending.

    self.push()

  def endElement(self, name):
    event = (self.stack_level, name)
    if DEBUG: logging.debug('End stack level %r', event)

    content = self.pop()
    if content:
      self.emit('>')
      self.emit(content)
      self.emit(['</', name, '>'])
    else:
      # No content means this element should be immediately closed.
      self.emit('/>')

    self.handleEvent(event, content)
    self.stack_level -= 1

  def characters(self, content):
    # The SAX parser will try to escape XML entities (like &amp;) and other
    # fun stuff. But this is not what we actually want. We want the original
    # content to be reproduced exactly as we received it, so we can pass it
    # along to others. The reason is simple: reformatting the XML by unescaping
    # certain data may cause the resulting XML to no longer validate.
    self.emit(xml.sax.saxutils.escape(content))


def strip_whitespace(enclosing_tag, all_parts):
  """Strips the whitespace from a SAX parser list for a feed.

  Args:
    enclosing_tag: The enclosing tag of the feed.
    all_parts: List of SAX parser elements.

  Returns:
    header_footer for those parts with trailing whitespace removed.
  """
  if 'feed' in enclosing_tag:
    first_part = ''.join(all_parts[:-3]).strip('\n\r\t ')
    return '%s\n</%s>' % (first_part, enclosing_tag)
  else:
    first_part = ''.join(all_parts[:-3]).strip('\n\r\t ')
    channel_part = first_part.rfind('</channel>')
    if channel_part == -1:
      raise Error('Could not find </channel> after trimming whitespace')
    stripped = first_part[:channel_part].strip('\n\r\t ')
    return '%s\n</channel>\n</%s>' % (stripped, enclosing_tag)

#SMOB: Start code to extract the queries from the content 
def remove_accessspace(feed_content, format):
  """Removes the sparql queries for each of the entry_id and pushes it into the MAP.

  
  Args:
    feed_content:  Content of the feed from which the queries are extracted
    format: format of the content rss/atom
  Returns: returned content without the queries
  
  TODO: Need to check if there is any difference in xml based on the formats  
  """
  
  
  """ Pavan: I tried using the xml.dom here but returned some parsing error
      NOW: Works with regular expression string manipulation
      TODO: Sophisticated way to parse the xml and remove an Element from it
  dom = xml.dom.minidom.parseString(feed_content)
  items = dom.getElementsByTagName('slideshow')
  for item in items:
    access_spaces = items.getElementsByTagName('access')
    for access_space in access_spaces:
        item.removeChild(access_space)
        
  return dom.toxml()"""
  
  content_array = re.split('<access>.*</access>', feed_content)
  content = ''
  for c in content_array:
    content += c
  return content
  
#SMOB: End code

class AtomFeedHandler(FeedContentHandler):
  """Sax content handler for Atom feeds."""

  def handleEvent(self, event, content):
    #SMOB: Logging to see content of each feed
    #logging.info('content: %r', content)
    depth, tag = event[0], event[1].lower()
    if depth == 1:
      if tag != 'feed' and not tag.endswith(':feed'):
        raise Error('Enclosing tag is not <feed></feed>. Found: %r' % tag)
      else:
        self.header_footer = strip_whitespace(event[1], self.pop())
    elif depth == 2 and (tag == 'entry' or tag.endswith(':entry')):
      entry = ''.join(self.pop())  
      #self.entries_map[self.last_id] = ''.join(self.pop())
      #SMOB: Start code to remove the access_space
      self.entries_map[self.last_id] = remove_accessspace(''.join(self.pop()), 'atom')
      #SMOB: End 
    elif depth == 3 and (tag == 'id' or tag.endswith(':id')):
      self.last_id = ''.join(content).strip()
      self.emit(self.pop())
    #SMOB: Start code, 
    #TODO: Replace this below code with that of the RSS Handler
    #elif depth == 3 and (tag == 'access' or tag.endswith(':access')):
      #self.entries_restrictions_map[self.last_id] = ''.join("""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?s FROM <http://localhost:8890/DAV/home/smob> WHERE { ?s ?p ?q }""")
      #self.emit(self.pop())
      #SMOB: End code
    #SMOB: Start code to add the entry restrictions
    elif (tag == 'space' or tag.endswith(':space')) and (
        depth == 5 or (depth == 4 and 'rdf' in self.enclosing_tag)):
      access_queries = []
      restriction = ''.join(content).strip()
      item_id = (self.last_id or self.last_link or
                 self.last_title or self.last_description)
      for id, queries in self.entries_restrictions_map.iteritems():
        if(id == item_id):
            access_queries = queries
      access_queries.append(restriction);
      self.entries_restrictions_map[item_id] = access_queries
      self.emit(self.pop())
    
    else:
      self.emit(self.pop())


class RssFeedHandler(FeedContentHandler):
  """Sax content handler for RSS feeds."""

  def handleEvent(self, event, content):
    depth, tag = event[0], event[1].lower()
    if depth == 1:
      if (tag != 'rss' and not tag.endswith(':rss')
          and tag != 'rdf' and not tag.endswith(':rdf')):
        raise Error('Enclosing tag is not <rss></rss> or <rdf></rdf>. '
                    'Found: %r' % tag)
      else:
        self.header_footer = strip_whitespace(event[1], self.pop())
    elif (tag == 'item' or tag.endswith(':item')) and (
        depth == 3 or (depth == 2 and 'rdf' in self.enclosing_tag)):
      item_id = (self.last_id or self.last_link or
                 self.last_title or self.last_description)
      #SMOB: Removing the access_space before adding this to the entry payloads
      self.entries_map[item_id] = remove_accessspace(''.join(self.pop()), 'rss') 
      #SMOB: Start code, adding the SPARQL queries to each entry_id
      #self.entries_restrictions_map[item_id] = ''.join('select ?s where {?s ?p ?o}')
      #SMOB: End code
      self.last_id, self.last_link, self.last_title, self.last_description = (
          '', '', '', '')
    elif (tag == 'guid' or tag.endswith(':guid')) and (
        depth == 4 or (depth == 3 and 'rdf' in self.enclosing_tag)):
      self.last_id = ''.join(content).strip()
      self.emit(self.pop())
    elif (tag == 'link' or tag.endswith(':link')) and (
        depth == 4 or (depth == 3 and 'rdf' in self.enclosing_tag)):
      self.last_link = ''.join(content).strip()
      self.emit(self.pop())
    elif (tag == 'title' or tag.endswith(':title')) and (
        depth == 4 or (depth == 3 and 'rdf' in self.enclosing_tag)):
      self.last_title = ''.join(content).strip()
      self.emit(self.pop())
    elif (tag == 'description' or tag.endswith(':description')) and (
        depth == 4 or (depth == 3 and 'rdf' in self.enclosing_tag)):
      self.last_description = ''.join(content).strip()
      self.emit(self.pop())
    #SMOB: Start code to add the entry restrictions
    elif (tag == 'space' or tag.endswith(':space')) and (
        depth == 5 or (depth == 4 and 'rdf' in self.enclosing_tag)):
      restriction = ''.join(content).strip()
      access_queries = []
      item_id = (self.last_id or self.last_link or
                 self.last_title or self.last_description)
      for id, queries in self.entries_restrictions_map.iteritems():
        if(id == item_id):
            access_queries = queries
      access_queries.append(restriction);
      self.entries_restrictions_map[item_id] = access_queries
      self.emit(self.pop())
    #elif (tag == 'access' or tag.endswith(':access')) and (
    #    depth == 4 or (depth == 3 and 'rdf' in self.enclosing_tag)):
    #  restriction = ''.join(content).strip()
    #  logging.info('Restriction: %r', restriction)
    #  self.entries_restrictions_map[self.last_link] = ''.join(content).strip()
    #  self.emit(self.pop())'''
    #SMOB: End code
    else:
      self.emit(self.pop())


def filter(data, format):
  """Filter a feed through the parser.

  Args:
    data: String containing the data of the XML feed to parse.
    format: String naming the format of the data. Should be 'rss' or 'atom'.

  Returns:
    Tuple (header_footer, entries_map) where:
      header_footer: String containing everything else in the feed document
        that is specifically *not* an <entry> or <item>.
      entries_map: Dictionary mapping entry_id to the entry's XML data.

  Raises:
    xml.sax.SAXException on parse errors. feed_diff.Error if the diff could not
    be derived due to bad content (e.g., a good XML doc that is not Atom or RSS)
    or any of the feed entries are missing required fields.
  """
  data_stream = cStringIO.StringIO(data)
  parser = xml.sax.make_parser()

  if format == 'atom':
    handler = AtomFeedHandler(parser)
  elif format == 'rss':
    handler = RssFeedHandler(parser)
  else:
    raise Error('Invalid feed format "%s"' % format)

  parser.setContentHandler(handler)
  parser.setEntityResolver(TrivialEntityResolver())
  # NOTE: Would like to enable these options, but expat (which is all App Engine
  # gives us) cannot report the QName of namespace prefixes. Thus, we have to
  # work around this to preserve the document's original namespacing.
  # parser.setFeature(xml.sax.handler.feature_namespaces, 1)
  # parser.setFeature(xml.sax.handler.feature_namespace_prefixes, 1)
  try:
    parser.parse(data_stream)
  except IOError, e:
    raise Error('Encountered IOError while parsing: %s' % e)

  for entry_id, content in handler.entries_map.iteritems():
    if format == 'atom' and not entry_id:
      raise Error('<entry> element missing <id>: %s' % content)
    elif format == 'rss' and not entry_id:
      raise Error('<item> element missing <guid> or <link>: %s' % content)
  #SMOB: Start code to return the entries_restrictions_map
  return handler.header_footer, handler.entries_map, handler.entries_restrictions_map
  #SMOB: End code

__all__ = ['filter', 'DEBUG', 'Error']
