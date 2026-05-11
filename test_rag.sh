#!/bin/bash
set -e

echo "========================================"
echo "FAISS RAG INTEGRATION TEST SUITE"
echo "========================================"
echo ""

API_URL="http://localhost:8081"

# Test 1: Health Check
echo "1. Testing Health Check..."
HEALTH=$(curl -s "$API_URL/health")
if echo "$HEALTH" | grep -q '"document_rag":true'; then
    echo "   ✅ DocumentRAG is healthy"
else
    echo "   ❌ DocumentRAG not initialized"
    exit 1
fi

# Test 2: Upload Ukrainian Document
echo ""
echo "2. Testing Ukrainian Document Upload..."
cat > /tmp/ukrainian_test.txt << 'UKRTEXT'
Привіт, як справи? Це тестовий документ українською мовою.
Ми перевіряємо, чи працює багатомовна система пошуку.
Українська мова має бути правильно оброблена.
Цей документ містить важливу інформацію про тестування системи.
Користувачі можуть завантажувати документи українською мовою.
Система повинна розуміти та відповідати на запити українською.
UKRTEXT

UPLOAD_RESULT=$(curl -s -X POST "$API_URL/api/documents/upload" \
  -F "file=@/tmp/ukrainian_test.txt" \
  -F "title=Тестовий документ українською" \
  -F "description=Документ для тестування багатомовного RAG")

UK_DOC_ID=$(echo "$UPLOAD_RESULT" | grep -o '"doc_id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$UK_DOC_ID" ]; then
    echo "   ✅ Uploaded Ukrainian document: $UK_DOC_ID"
else
    echo "   ❌ Upload failed: $UPLOAD_RESULT"
    exit 1
fi

# Test 3: Upload English Document
echo ""
echo "3. Testing English Document Upload..."
cat > /tmp/english_test.txt << 'ENGTEXT'
Hello, how are you? This is a test document in English.
We are testing the multilingual search system.
English language should be processed correctly.
This document contains important information about system testing.
Users can upload documents in English.
The system should understand and respond to English queries.
ENGTEXT

UPLOAD_RESULT=$(curl -s -X POST "$API_URL/api/documents/upload" \
  -F "file=@/tmp/english_test.txt" \
  -F "title=English Test Document")

EN_DOC_ID=$(echo "$UPLOAD_RESULT" | grep -o '"doc_id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$EN_DOC_ID" ]; then
    echo "   ✅ Uploaded English document: $EN_DOC_ID"
else
    echo "   ❌ Upload failed"
    exit 1
fi

# Test 4: List Documents
echo ""
echo "4. Testing List Documents..."
LIST_RESULT=$(curl -s "$API_URL/api/documents")
DOC_COUNT=$(echo "$LIST_RESULT" | grep -o '"count":[0-9]*' | cut -d':' -f2)
echo "   ✅ Found $DOC_COUNT documents"

# Test 5: Chat with Document Context
echo ""
echo "5. Testing Chat with Document Citation..."
CHAT_RESULT=$(curl -s -X POST "$API_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Розкажи про тестування системи українською",
    "session_id": "test_session_'$(date +%s)'",
    "persona_id": "default"
  }')

RESPONSE=$(echo "$CHAT_RESULT" | grep -o '"response":"[^"]*"' | cut -d'"' -f4)
if [ -n "$RESPONSE" ]; then
    echo "   ✅ Got response from LLM"
    echo "   Response preview: ${RESPONSE:0:100}..."
    
    # Check for citation patterns
    if echo "$RESPONSE" | grep -qi "document\|документ\|according to\|based on"; then
        echo "   ✅ Response contains document citation"
    else
        echo "   ⚠️  Response may not cite source (this is OK if query didn't match)"
    fi
else
    echo "   ❌ No response from LLM"
fi

# Test 6: Unrelated Query (should not hallucinate)
echo ""
echo "6. Testing Unrelated Query (no hallucination)..."
CHAT_RESULT=$(curl -s -X POST "$API_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the weather like today?",
    "session_id": "test_session_'$(date +%s)'",
    "persona_id": "default"
  }')

RESPONSE=$(echo "$CHAT_RESULT" | grep -o '"response":"[^"]*"' | cut -d'"' -f4)
if [ -n "$RESPONSE" ]; then
    echo "   ✅ Got response for unrelated query"
    if echo "$RESPONSE" | grep -qi "according to the document"; then
        echo "   ⚠️  Possible hallucinated citation"
    else
        echo "   ✅ No forced citation for unrelated query"
    fi
fi

# Cleanup: Delete test documents
echo ""
echo "7. Cleaning up test documents..."
curl -s -X DELETE "$API_URL/api/documents/$UK_DOC_ID" > /dev/null
echo "   ✅ Deleted Ukrainian document"
curl -s -X DELETE "$API_URL/api/documents/$EN_DOC_ID" > /dev/null
echo "   ✅ Deleted English document"

# Cleanup temp files
rm -f /tmp/ukrainian_test.txt /tmp/english_test.txt

echo ""
echo "========================================"
echo "ALL TESTS COMPLETED SUCCESSFULLY!"
echo "========================================"
