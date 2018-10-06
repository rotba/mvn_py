/**
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.tika.parser;

import java.io.IOException;
import java.io.InputStream;
import java.io.StringWriter;

import org.apache.oro.text.regex.MalformedPatternException;
import org.apache.tika.exception.TikaException;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.sax.TeeContentHandler;
import org.apache.tika.sax.WriteOutContentHandler;
import org.apache.tika.utils.RegexUtils;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;

/**
 * Parser decorator that post-processes the results from a decorated parser.
 * The post-processing takes care of filling in any "fulltext", "summary", and
 * regexp {@link Content} objects with the full text content returned by
 * the decorated parser. The post-processing also catches and logs any
 * exceptions thrown by the decorated parser.
 */
public class ParserPostProcessor extends ParserDecorator {

    private static final String LINK_PATTERN =
        "([A-Za-z][A-Za-z0-9+.-]{1,120}:"
        + "[A-Za-z0-9/](([A-Za-z0-9$_.+!*,;/?:@&~=-])|%[A-Fa-f0-9]{2}){1,333}"
        + "(#([a-zA-Z0-9][a-zA-Z0-9$_.+!*,;/?:@&~=%-]{0,1000}))?)";

    /**
     * Creates a post-processing decorator for the given parser.
     *
     * @param parser the parser to be decorated
     */
    public ParserPostProcessor(Parser parser) {
        super(parser);
    }

    /**
     * Forwards the call to the delegated parser and post-processes the
     * results as described above.
     */
    public void parse(
            InputStream stream, ContentHandler handler, Metadata metadata)
            throws IOException, SAXException, TikaException {
        StringWriter writer = new StringWriter();
        handler = new TeeContentHandler(
                handler, new WriteOutContentHandler(writer));
        super.parse(stream, handler, metadata);

        String content = writer.toString();
        metadata.set("fulltext", content);

        int length = Math.min(content.length(), 500);
        metadata.set("summary", content.substring(0, length));

        try {
            for (String link : RegexUtils.extract(content, LINK_PATTERN)) {
                metadata.add("outlinks", link);
            }
        } catch (MalformedPatternException e) {
            throw new TikaException("Malformed URL pattern", e);
        }
    }

}
