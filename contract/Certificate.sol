// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CertificateRegistry {
    address public owner;

    struct Certificate {
        string studentId;
        string studentName;
        string department;
        string certHash;
        uint256 timestamp;
        bool isValid;
    }

    // Mapping certHash -> Certificate
    mapping(string => Certificate) public certificates;

    event CertificateIssued(string indexed certHash, string studentId, string studentName, uint256 timestamp);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner/admin can perform this action");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function issueCertificate(
        string memory _studentId,
        string memory _studentName,
        string memory _department,
        string memory _certHash
    ) public onlyOwner {
        require(!certificates[_certHash].isValid, "Certificate hash already exists");
        
        certificates[_certHash] = Certificate({
            studentId: _studentId,
            studentName: _studentName,
            department: _department,
            certHash: _certHash,
            timestamp: block.timestamp,
            isValid: true
        });

        emit CertificateIssued(_certHash, _studentId, _studentName, block.timestamp);
    }

    function verifyCertificate(string memory _certHash) public view returns (
        bool isValid,
        string memory studentId,
        string memory studentName,
        string memory department,
        uint256 timestamp
    ) {
        Certificate memory cert = certificates[_certHash];
        return (cert.isValid, cert.studentId, cert.studentName, cert.department, cert.timestamp);
    }
}